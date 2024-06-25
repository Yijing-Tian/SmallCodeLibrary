'''
批量删除，指定发件人的所有邮件
'''
import imaplib

# 登录信息
username = "地址@qq.com"  # 替换为你的QQ邮箱地址
password = ""  # 登录QQ邮箱官网，进入“设置” -> “账户” -> “POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务”。
mail = imaplib.IMAP4_SSL("imap.qq.com") # 连接到QQ邮箱的IMAP服务器，正常情况下不需要做修改
mail.login(username, password) # 登录邮箱
mail.select("INBOX") # 选择邮箱文件夹，"INBOX"代表收件箱，正常情况下不需要做修改

# 搜索邮件（按发件人）
sender_email = "地址@qq.com"  # 替换为目标发件人的邮箱地址
status, search_data = mail.search(None, f'FROM "{sender_email}"')

# 检查是否找到邮件
if status == "OK":
    email_ids = search_data[0].split()

    # 遍历所有找到的邮件并删除
    for email_id in email_ids:
        # 标记邮件为删除状态
        mail.store(email_id, "+FLAGS", "\\Deleted")

    # 执行删除操作
    mail.expunge()

    print(f"成功删除了{len(email_ids)}封来自{sender_email}的邮件。")
else:
    print("未找到来自该发件人的邮件。")

# 关闭与服务器的连接
mail.close()
mail.logout()


'''
发送邮件
'''
from email.mime.text import MIMEText
import smtplib

def mailToMe (subject): # 主题
    mail_txt = "" # 邮箱内容
    from_email_address = "l1071812516@163.com" # 发送邮箱地址
    password = '' # 登录QQ邮箱官网，进入“设置” -> “账户” -> “POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务”。
    to_mail_address = '1071812516@qq.com' # 接收邮箱地址
    message = MIMEText(mail_txt, 'plain', 'utf-8')
    message['Subject'] = subject
    message['To'] = to_mail_address
    message["From"] = from_email_address
    smtp = smtplib.SMTP_SSL('smtp.163.com', 994)
    smtp.login(from_email_address, password)
    smtp.sendmail(from_email_address, [to_mail_address], message.as_string())
    smtp.close()


mailToMe ("发送内容")

