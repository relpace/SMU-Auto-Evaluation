import configparser
import json
import logging
import os
import re
import time
from io import BytesIO
import muggle_ocr
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
from bs4 import BeautifulSoup

captcha_url = "http://zhjw.smu.edu.cn/yzm?d="
login_url = "http://zhjw.smu.edu.cn/new/login"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Host": "zhjw.smu.edu.cn",
    "Referer": "http://zhjw.smu.edu.cn/",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

logging.basicConfig(
    filename="evaluation.log",
    filemode='w',
    format='%(asctime)s | %(levelname)s:  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,)


# 加密密码
def encrypt_password(password, verifycode):
    # 将验证码重复四次作为密钥
    key = (verifycode * 4).encode('utf-8')
    # AES要求key和data的长度必须是16的倍数
    cipher = AES.new(key, AES.MODE_ECB)
    # 加密密码
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    # 将加密后的密码转换为十六进制字符串
    return encrypted.hex()


# 获取验证码
def get_captcha(session):
    captcha_response = session.get(captcha_url + str(int(time.time() * 1000)), headers=headers)
    img = Image.open(BytesIO(captcha_response.content))
    temp_save_path = 'captcha.png'
    img.save(temp_save_path)
    print(f"验证码图片临时保存至: {temp_save_path}")
    with open(r"captcha.png", "rb") as f:
        img_bytes = f.read()
    sdk = muggle_ocr.SDK(model_type=muggle_ocr.ModelType.Captcha)
    text = sdk.predict(image_bytes=img_bytes)
    temp_save_path = 'captcha.png'
    if os.path.exists(temp_save_path):
        os.remove(temp_save_path)
        print(f"临时文件 {temp_save_path} 已删除")
    return text
    '''
    img.show()
    captcha = input("请输入验证码: ")
    return captcha
    '''


# 登录
def login(account, password, captcha, session):
    encrypted_password = encrypt_password(password, captcha)
    data = {
        "account": account,
        "pwd": encrypted_password,
        "verifycode": captcha
    }
    response = session.post(login_url, data=data, headers=headers)
    if response.status_code == 200 and "成功" in response.text:
        logging.info("登陆成功")
        print(response.url)
        get_courses(session)
    else:
        logging.error(msg="登录失败，原因： " + response.text)


def test(session):
    response = session.get("http://zhjw.smu.edu.cn/new/welcome.page", headers=headers)
    print(response.text)
    print(response.url)


import requests


def evaluate_course(session, teadm, dgksdm, ktpj):
    eval_url = f"http://zhjw.smu.edu.cn/new/student/ktpj/showXsktpjwj.page?pjlxdm=6&teadm={teadm}&dgksdm={dgksdm}&wjdm={ktpj}"
    # 访问评价页面
    eval_response = session.get(eval_url, headers=headers, )
    soup = BeautifulSoup(eval_response.content, 'lxml')
    scripts = soup.find_all('script')
    for script in scripts:
        if "entss.post" in script.text:
            matches = re.findall(r"(\w+):'([^']+)'", script.text)
            data = {match[0]: match[1] for match in matches}
            print(data['teaxm'], data['kcrwdm'], data['kcptdm'], data['kcdm'], data['pjlxdm'])
    save_url = "http://zhjw.smu.edu.cn/new/student/ktpj/savePj"

    questions = soup.find_all('div', class_='question')
    data_list = []
    count = 0
    for question in questions:
        txdm = int(question['data-txdm'])
        zbdm = question['data-zbdm']
        zbmc = question.find('h3').get_text(strip=True).replace("\n", "").replace("\t", "")
        # 对于选择题和非选择题的处理
        if question.find('div', class_='raty'):
            # 处理有评分选项的问题
            raty_div = question.find('div', class_='raty')
            options = json.loads(raty_div['data-wtxm'])
            zbxmdm = options[-2]['zbxmdm']  # 比较满意
            fz = 20
            dtjg = "★★★★"
        elif question.find('input', type='radio') and txdm != 3:
            # 处理选择题，例如是/否的单选题
            radio_inputs = question.find_all('input', type='radio')
            zbxmdm = radio_inputs[-1]['value']
            fz = 0
            dtjg = "否"
        if count == 5:
            break
        data_list.append({
            "txdm": txdm,
            "zbdm": zbdm,
            "zbmc": zbmc,
            "zbxmdm": zbxmdm,
            "fz": fz,
            "dtjg": dtjg
        })
        count += 1

    # 将数据列表转换为JSON格式
    json_output = json.dumps(data_list, ensure_ascii=False, indent=4)
    logging.info(json_output)

    dataa = {
        'xnxqdm': data['xnxqdm'],
        'pjlxdm': data['pjlxdm'],
        'teadm': teadm,  # 教师代码
        'teabh': teadm,  # 教师编号
        'teaxm': data['teaxm'],  # 教师姓名
        'wjdm': data['wjdm'],  # 问卷代码
        'kcrwdm': data['kcrwdm'],  # 课程任务代码
        'kcptdm': data['kcptdm'],  # 课程平台代码
        'kcdm': data['kcdm'],  # 课程代码
        'dgksdm': dgksdm,  # 大纲课时代码
        'jxhjdm': data['jxhjdm'],  # 教学环节代码
        'wtpf': '80',  # 问卷评分
        'pfsm': '',  # 评分说明
        # 根据实际页面中的题目结构构造dt字段
        'dt': json_output
    }
    response = session.post(save_url, data=dataa, headers=headers)
    logging.info(response.text)


def get_courses(session):
    # 获取课程信息
    url = "http://zhjw.smu.edu.cn/new/student/ktpj/xsktpjData"
    data = {'jsrq': '',
            'page': 1,
            'rows': 20,
            'sort': 'jsrq, jcdm2',
            'order': 'desc'}
    response = session.post(url, headers=headers, data=data)
    courses_info = response.json()
    logging.info(courses_info)
    # 遍历课程信息
    for course in courses_info['rows']:
        # 检查课程是否未评价
        if course['pjdm'] == '':
            teadm = course['teadm']
            dgksdm = course['dgksdm']
            ktpj = course['ktpj']
            # 调用处理未评价课程的函数
            evaluate_course(session, teadm, dgksdm, ktpj)


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    account = config.get('login', 'account')
    password = config.get('login', 'password')
    session = requests.Session()
    captcha = get_captcha(session)
    login(account, password, captcha, session)


if __name__ == "__main__":
    main()
