from functools import wraps
import random
import sqlite3
import traceback
from flask import Flask,jsonify, request
from flask_cors import CORS, cross_origin
import os
import datetime
import pandas as pd

import jwt
app=Flask(__name__)
CORS(app)
app.secret_key="7ea555fa5f8f47238a4b798c33ca6e85"
filepath="/home/smallsaravanan8/service/static/image"
def databaseConn(commen,val):
    conn = sqlite3.connect('data.db')
    conn.execute(f'create table  if not exists adminlogin(client_id text,otp text,token text)')
    cursorObj = conn.cursor()
    cursorObj.execute(commen,val)
    data=cursorObj.fetchone()
    conn.commit()
    conn.close()
    return data
def auth(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token=request.headers['Authorization']
        if not token:
            return jsonify({'emsg': 'a valid token is missing'})
        try:
            token_decode=jwt.decode(token,app.secret_key, algorithms=["HS256"],verify=False)
            # conn = sqlite3.connect('otp.db')
            # cursorObj = conn.cursor()
            clientTokenCom="select * from  adminlogin where userId = ?"
            clientToken=(token_decode['user'],)
            data=databaseConn(clientTokenCom,clientToken)
            # conn.commit()
            if data[2] != token:
                 return jsonify({"emsg":"Token not valid"})
        except Exception as error:
            return jsonify({"emsg":"Token not valid"})
        return f(*args, **kwargs)
    return decorator
@app.route('/otpsend',methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def otpsend():
    client=request.get_json()["userId"]
    try:
        if client:
            otp=random.randint(10000,99999)
            print(otp)
            #main=smtplib.SMTP_SSL("smtp.gmail.com",465)
            # send="saravanan.r@zebuetrade.com"
            # password="Sarbvc7337#"
            # rec="dhatshanamoorthy2001@gmail.com"
            # msg=f'Your OTP is {otp}'
            # main.login(send,password)
            # main.sendmail(send,rec,msg)
            # print("Mail send Successfully")
            #main.quit()
            # conn = sqlite3.connect('otp.db')
            # cursorObj = conn.cursor()
            dateto=datetime.datetime.now()+ datetime.timedelta(minutes=3)
            dateto_str=dateto.strftime("%Y-%m-%d %H:%M:%S")
            checkIdCom="select * from  adminlogin where userId = ?"
            checkId=(client,)
            data=databaseConn(checkIdCom,checkId)
            if data:
                idUpdateCom='UPDATE adminlogin SET otp=? ,timestamp=?,count=? WHERE userId=?'
                idUpdate=(otp,dateto_str,0 ,client)
                databaseConn(idUpdateCom,idUpdate)
            else:
                idInserCom='insert into adminlogin values(?,?,?,?)'
                idInsert=(client,otp,None,dateto_str,0)
                databaseConn(idInserCom,idInsert)
                
            # conn.commit()
            # conn.close()
            return jsonify({"msg":"OTP send successfully"})
        else:
            return jsonify({"emsg":"Invaild Client ID "})
    except :
        print(traceback.print_exc())
        return jsonify({"emsg":"SQL  DATABASE ERROR "})

@app.route("/otpverify",methods=['GET','POST'])
def otpverify():
    client=request.get_json()["userId"]
    otp=request.get_json()["otp"]
    # conn = sqlite3.connect('otp.db')
    # cur = conn.cursor()
    clientOtpcom="select * from  adminlogin where userId = ?"
    clientOtp=(client,)
    data=databaseConn(clientOtpcom,clientOtp)
    # conn.commit()
    # conn.close()
    print()
    time_threshold = datetime.datetime.now() 
    time_threshold_str = time_threshold.strftime("%Y-%m-%d %H:%M:%S")
    if data:
        if int(data[4])<=2:
            updateCouCom="update adminlogin SET count=? WHERE userId=?"
            updateCou=int(data[4])
            countval=(updateCou+1,client)
            databaseConn(updateCouCom,countval)
            if  time_threshold_str <= data[3]:
                if int(data[1])== int(otp):
                    token=jwt.encode({
                        'user':client,
                        'exp':datetime.datetime.utcnow() + datetime.timedelta(hours=5)
                    }, key=app.secret_key)
                    # conn = sqlite3.connect('otp.db')
                    # cursorObj = conn.cursor()
                    verifySucCom='UPDATE adminlogin SET token=? WHERE userId=?'
                    verifySuc=(token,client)
                    databaseConn(verifySucCom,verifySuc)
                    # conn.commit()
                    # conn.close()
                    return jsonify({"msg":"OTP verified ","token":token})
                
                else:
                    return jsonify({"emsg":"OTP Not  valid"})
            else:
                return jsonify({"emsg":"OTP is expried"})
        else:
            
            return jsonify({"emsg":"you're 3 times above enter wrong OTP"})
    else:
        return jsonify({"emsg":"Client not valid"})

@app.route("/getData",methods=["post"])
@cross_origin(supports_credentials=True)
def getData():
    data=request.get_json()
    try:
        print(data)
        con=sqlite3.connect("data.db")
        con.execute("CREATE TABLE IF NOT EXISTS admin_details (id     INTEGER PRIMARY KEY AUTOINCREMENT,name   TEXT,email  TEXT,mobile TEXT,image  TEXT)")
        con.commit()
        con.execute("CREATE TABLE  IF NOT EXISTS adminlogin (userId    TEXT,otp       TEXT,token     TEXT,timestamp TEXT,count     TEXT)")

        user=con.execute("select * from admin_details where id='"+data['id']+"'").fetchall()
        con.commit()
        con.close()
        if user != []:
            id=user[0][0]
            name=user[0][1]
            email=user[0][2]
            mobile=user[0][3]
            image=user[0][4]
            if image:
                image="/static"+image.split("/static")[1]

            return jsonify({"msg":"success","mobile":mobile,"email":email,"image":image,"name":name,"id":id})
        else:
            print(user)
            return jsonify({"msg":"No data"})
    except Exception as e:
        print(traceback.print_exc())
        
@app.route("/updateData",methods=["post","PUT", "DELETE"])
@auth
@cross_origin(supports_credentials=True)
def updateData():
    data=request.form
    try:
        print("data::::::::",data)
        con=sqlite3.connect("data.db")
        cursor=con.cursor()
        id=str(data['id'])
        chk = (os.path.isdir(filepath+"/"+str(data['mobile'])))
        if chk == False:
            try:
                os.mkdir(filepath+"/"+str(data['mobile']))
            except:
                pass
        image_file = request.files.get('image')
        print(image_file)
        
        imageFileName = image_file.filename
        print(imageFileName)
        image_file.save(filepath+"/"+data['mobile']+"/"+imageFileName)
        save_file=filepath+"/"+data['mobile']+"/"+imageFileName
        cursor.execute("update admin_details set mobile='"+data['mobile']+"',email='"+data['email']+"',image='"+save_file+"' where id='"+id+"'")
        con.commit()
        user=con.execute("select * from admin_details where id='"+id+"'").fetchall()
        con.close()
        if user != []:
            id=user[0][0]
            name=user[0][1]
            email=user[0][2]
            mobile=user[0][3]
            image=user[0][4]
            if image:
                image="/static"+image.split("/static")[1]
            print(name,email,mobile,image)
            return jsonify({"msg":"success","mobile":mobile,"email":email,"image":image,"name":name,"id":id})
        else:
            print(user)
            return jsonify({"msg":"No data"})
    except Exception as e:
        print(traceback.print_exc())
        return jsonify({"msg":"failed"})


@app.route("/register",methods=["POST"])
@cross_origin(supports_credentials=True)
def register():
    data=request.get_json()
    try:
        
        moblie=data['mobile']
        uname=data['uname']
        email=data['email']
        print(moblie,uname,email)
        
        con=sqlite3.connect("data.db")
        df=pd.read_sql_query("select * from admin_details",con)
        moblie_exsists=df['mobile'].eq(moblie).any()
        if moblie_exsists:
            return jsonify({"msg":"Already mobile number exsist"})
        cursor=con.cursor()
        cursor.execute("insert into admin_details (name,email,mobile) values (?,?,?)",(uname,email,moblie))
        con.commit()
        return jsonify({"msg":"Successfull register"})
    except Exception as e:
        print(traceback.print_exc())
        return jsonify({"msg":"failed to register"})


if __name__=="__main__":
    app.run(debug=False,host="0.0.0.0")