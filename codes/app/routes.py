# -*- coding: utf-8 -*-  
#coding:utf8

from flask import render_template, url_for, flash, request, redirect
from app import app, db
from app.models import *
from app.forms import *
import time
from datetime import datetime
import os
import secrets
from PIL import Image
import boto3
from flask_login import login_user, current_user, logout_user, login_required
import json
# Essentially how we are going to write routes in general
import codecs
import sys
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

upload_bucket = 'mary-app-upload'
os.environ['LC_ALL'] = "en_US.UTF-8"

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

# save picture on s3
def save_picture(form_picture):
    s3 = boto3.resource('s3')

    # first: save it on local machine
    filename = form_picture.filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/upload/image', picture_fn)
    # output_size = (125, 125)
    i = Image.open(form_picture)
    # i.thumbnail(output_size)
    i.save(picture_path)

    # then: upload it to s3 bucket
    response = s3.meta.client.upload_file(os.path.join(app.root_path, 'static/upload/image', picture_fn), 
        upload_bucket,  
        "/".join(("image", picture_fn)))
    
    print(response)
    return picture_fn

# text detection
def textDetection(filename):
    client = boto3.client('rekognition', region_name='us-east-1')
    boto3.set_stream_logger('')
    response = client.detect_text(
        Image={        
            'S3Object': {
                'Bucket': upload_bucket,
                'Name': "/".join(("image", filename))
            }
        }
    )

    texts = response['TextDetections']
    result = ""

    # only output the lines
    for text in texts:
        if text['Type'] == 'LINE':
            result += text['DetectedText']
            result += " "
    
    return result

# translate text into target language
def translation(original,language):
    client = boto3.client('translate', region_name='us-east-1')
    response = client.translate_text(
        Text=original,
        SourceLanguageCode='en',
        TargetLanguageCode=language
    )
    return response['TranslatedText']

# [text detection]
@app.route("/detect", methods=['GET', 'POST'])
def detect():
    form = DetectForm()
    # get file, save the s3 url of it
    if form.validate_on_submit():
        # save it 
        flash('Your image has been sent to server! Please wait...', 'info')
        f = form.picture.data
        picture_file = save_picture(f)
        detect = Detect(image = picture_file)
        db.session.add(detect)
        db.session.commit()
        # flash('Your image has been sent to server! Please wait...', 'info')

        # detect
        # content = textDetection(picture_file)
        # translated = translation(content,form.data['language'])
        # return render_template('detect.html', form=form, title="Text Dectection",content=textDetection(picture_file), img = os.path.join(app.root_path, 'static/upload/image', picture_file),translate=translated)

        try:
            content = textDetection(picture_file)
            flash('Text detection completed!', 'success')
            print('Text detection completed!')
            # delete local file
            temp = os.path.join(app.root_path, 'static/upload/image', picture_file)
            os.remove(temp)
            print('Remove file completed!')

            # translate
            if form.data['language'] and form.data['language'] != 'null':
                translated = translation(content,form.data['language'])
                print('Translate completed!')
                return render_template('detect.html', form=form, title="Text Dectection",content=content, img = os.path.join(app.root_path, 'static/upload/image', picture_file),translate=translated)


            return render_template('detect.html', form=form, title="Text Dectection",content=content, img = os.path.join(app.root_path, 'static/upload/image', picture_file))
        except:
            flash('No text detected!', 'warning')
            return render_template('detect.html', form=form, title="Text Dectection",content="no text detected", img = os.path.join(app.root_path, 'static/upload/image', picture_file))

    return render_template('detect.html', form=form, title="Text Dectection")



# save picture on s3
def save_audio(form_audio):
    s3 = boto3.resource('s3')

    # first: save it on local machine
    filename = form_audio.filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(filename)
    audio_fn = random_hex + f_ext
    audio_path = os.path.join(app.root_path, 'static/upload/audio', audio_fn)
    form_audio.save(audio_path)
    print('save audio locally completed!')

    # then: upload it to s3 bucket
    response = s3.meta.client.upload_file(os.path.join(app.root_path, 'static/upload/audio', audio_fn), 
        upload_bucket,  
        "/".join(("audio", audio_fn)))
    
    print('upload to s3 completed')
    return audio_fn

# start a transcribe job, and return the job name
def perform_transcribe(email,title,filename):
    # create transcribe job
    client = boto3.client('transcribe', region_name='us-east-1')
    print(filename)
    _, f_ext = os.path.splitext(filename)

    # combine user email and title
    jobname = "-JOBNAME-".join((email,title))
    response = client.start_transcription_job(
        TranscriptionJobName = jobname,
        LanguageCode='en-AU',
        MediaFormat=f_ext.replace('.',''),
        Media={
            'MediaFileUri': "/".join(('s3://mary-app-upload/audio',filename))
        },
        OutputBucketName='mary-app-output'
    )
    return jobname

# add the job into dynamodb for certain user
def add_to_list(jobname):
    email,title = jobname.split("-JOBNAME-")
    dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
    table = dynamodb.Table('user')

    # try to search user in database
    response = table.get_item(
        Key={
            'email':email
        }
    )
    print('db response:')
    print(response)

    

    # if the list exists, so the user has already in the db, just append list
    if 'Item' in response:
        item = response['Item']
        original_list = item[u'lists']
        original_list.add(title)
        table.update_item(
            Key={
                'email': email
            },
            UpdateExpression='SET lists = :val1',
            ExpressionAttributeValues={
                ':val1': original_list
            }
        )
    else:
        table.put_item(
            Item={
                'email': email,
                'lists':{title}
            }
        )


# [transcribe]
@app.route("/transcribe", methods=['GET', 'POST'])
def transcribe():
    # authentication
    if current_user.is_authenticated:
        form = TranscribeForm()      
        if form.validate_on_submit():
            print('Form submitted completed!')
            flash('Your audio has been sent to server! Please wait...', 'info')
            f = form.audio.data

            # save file on S3
            audio_file = save_audio(f)   
            # title = form.title.data    
            # transcribe = Transcribe(title=title,audio = audio_file)
            # db.session.add(transcribe)
            # db.session.commit()
            print('Save audio completed!')

            # # using the file on S3 to create a new transcribe job
            jobname = perform_transcribe(str(current_user.id),form.title.data,audio_file)
            print('Perform tasks completed!')
            # delete local file
            temp = os.path.join(app.root_path, 'static/upload/audio', audio_file)
            os.remove(temp)
            print('Local audio removed completed!')
            
            # # store the job into job list of current user in dynamodb
            add_to_list(jobname)
            print("add to list successful!")

            flash('Your new transcribe job has been created! It often takes a while to finish the job, you can check it later in the list!', 'success')
            return redirect(url_for("home"))
        return render_template('transcribe.html', form=form, title="Transcribe")
    flash('Note: You have to login to use this function', 'info')
    return redirect(url_for("login"))


def getJobStatus(jobname):

    client = boto3.client('transcribe', region_name='us-east-1')

    # combine user email and title
    
    response = client.get_transcription_job(
        TranscriptionJobName = jobname
    )

    return response['TranscriptionJob']

def getJobList(email):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('user')
    response = table.get_item(
        Key={
            'email': email
        }
    )
    if 'Item' in response:
        jobs =  response['Item']['lists']
        result = []
        for job in jobs:
            jobname = "-JOBNAME-".join((email,job))
            response = getJobStatus(jobname)
            print(response)
            status = response['TranscriptionJobStatus']
            if status == 'COMPLETED':
                element = {'title':job,'status':status,'url':response['Transcript']['TranscriptFileUri']}
                result.append(element.copy())
            else:
                element = {'title':job,'status':status}
                result.append(element.copy())
        return result
    else:
        return None


# [check transcribtion list]
@app.route("/lists", methods=['GET', 'POST'])
def lists():
    # get all jobs from dynamodb
    if current_user.is_authenticated:
        jobs = getJobList(str(current_user.id))
        return render_template('lists.html', title="Lists", jobs=jobs)
    return redirect(url_for("home"))


# Login route 
@app.route("/login", methods=['GET', 'POST'])
def login():
    # if logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(email=form.email.data).first()
        if customer and customer.password == form.password.data:
            login_user(customer, remember=form.remember.data)
            flash(f"You're now logged in", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email and password combination.", "danger")
    return render_template("login.html", title="Log In", form=form)

# sign up
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    # if logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = SignUpForm()
    if form.validate_on_submit():
        customer = Customer(email=form.email.data, password=form.password.data)
        db.session.add(customer)
        db.session.commit()
        flash(f"Account successfully created!", "success")
        return redirect(url_for("home"))
    return render_template("signup.html", title="Sign Up", form=form)


# Logout route
@app.route("/logout")
def logout():
    logout_user()
    flash(f"You are now logged out.", "success")
    return redirect(url_for('home'))


def getTranscribeContentURL(jobname):
    client = boto3.client('transcribe', region_name='us-east-1')
    # combine user email and title
    
    response = client.get_transcription_job(
        TranscriptionJobName = jobname
    )
    return response['TranscriptionJob']['Transcript']['TranscriptFileUri']

# get the content of audio
def getContent(url):
    s3 = boto3.resource('s3')
    strings = url.split("/")
    filename = strings[-1]
    obj = s3.Object('mary-app-output', filename)
    # body = obj.get()['Body'].read()
    file_content = obj.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    # data = json.load(body)
    results = json_content['results']
    content = results['transcripts']
    return content[0]['transcript']


def generateLinkToS3(id,title,content,translated):
    s3 = boto3.resource('s3')

    print("original translated class:")
    print(translated.__class__)
    # generate local file
    filename = "-JOBNAME-".join((str(id),title))
    filename += '.txt'
    path = os.path.join(app.root_path,'static/result', filename)
    # create file locally
    f= open(path,"w+",encoding='utf-8')
    f.write("Original content: \n")
    f.write(content)
    f.write("\nTranslated content: \n")
    print("translated class:")
    print (translated.__class__)
    print("translated:")
    print(translated)
    f.write(translated)
    f.close

    f = open(path,"r",encoding='utf-8')
    print(f.read())
    f.close
    # upload to s3 and make it public
    upload_key = "/".join(("from-audio", filename))
    # print("path: "+os.path.join(app.root_path,'static\\result', filename))
    # print("upload key: " + upload_key)
    response = s3.meta.client.upload_file(
        os.path.join(app.root_path,'static/result', filename), 
        'mary-app-output',  
        upload_key,
        ExtraArgs={'ACL': 'public-read'}
    )

    # generte url of it
    url = "https://"+"mary-app-output.s3.amazonaws.com"+"/from-audio/"+filename
    return url


def sendEmail(id,email, url):
    # check topic
    target_topic = 'USERID-'+str(id)+'-'
    topicArn = ''
    client = boto3.client('sns',region_name='us-east-1')
    response = client.list_topics()
    for topic in response['Topics']:
        if target_topic in topic['TopicArn']:
            topicArn = topic['TopicArn']
            break

    # if topic is not created, then create and subscribe
    if topicArn == '':
        # create topic
        response = client.create_topic(
            Name=target_topic
        )
        # print(response)

        # get topic arn from response
        topicArn = response['TopicArn']

        # send subscription link
        response = client.subscribe(
            TopicArn=topicArn,
            Protocol='email',
            Endpoint=email
        )
        # print(response)
        return "first"
    # topic created
    else:
        # check subscription
        response = client.list_subscriptions_by_topic(
            TopicArn=topicArn
        )
        # print(response)

        status = response['Subscriptions'][0]['SubscriptionArn']

        # if not subscribe, resend link
        if status == 'PendingConfirmation':
            response = client.subscribe(
                TopicArn=topicArn,
                Protocol='email',
                Endpoint=email
            )
            print(response)
            return "pending"
        # subscribed
        else:
            response = client.publish(
                TopicArn=topicArn,
                Message='url:'+url,
                Subject='Your transcription and translation job ready to download',
            )
            return "success"




# show specific job
@app.route('/job/<title>',methods=['GET', 'POST'])
def job(title):
    if current_user.is_authenticated:
        form = JobForm()
        jobname = "-JOBNAME-".join((str(current_user.id),title))
        url = getTranscribeContentURL(jobname)
        content = getContent(url)

        # form2 = GetFileForm(prefix='form2')
        # translated = ""
        # do translation work
        if form.validate_on_submit:
            if form.data['language'] and form.data['language'] != 'null':
                translated = translation(content,form.data['language'])
                # form.contentTest.data = content
                print(translated.__class__)
                print(translated)

                url = generateLinkToS3(current_user.id,title,content,translated)
                response = sendEmail(current_user.id,current_user.email,url)
                if response == "first":
                    flash("Please subscribe for first time!","info")
                if response == "pending":
                    flash("Please comfirm subscription! The confirmation link has been re-sent to your email address!","danger")
                if response == "success":
                    flash("The link has been sent to your email address! It may takes several minutes to receive it, please wait a while ...","success")
                return render_template('job.html', form=form, title="Job",content=content,translate=translated)

        # check whether want to download file
        
        # print(request.form['content'])
        # if form2.validate_on_submit:
        #     if form.request['']
            
        return render_template("job.html", title="Job", form=form, content=content)
    return redirect(url_for('home'))
    


