# Cloud Computing Project

[TOC]

## **Description:**

- The core functions of the web application is to obtain text content inside the 
most common media files(images and audios) and translate it to other languages.

- Not only neat printing text can be detected, the system can also give detect text 
from handwriting and irregular printing layout.

- All the transcription requests by user will be stored, user can check the content
multiple times without uploading the audio files again.

- The translated content of transcription result will generate a file, and the 
download link will be sent to user's mailbox. (Note: the user has to confirm 
subscription first.)

---

> **Public link:**
> ~~http://project-env.eba-zysihajv.us-east-1.elasticbeanstalk.com/~~
>
> > (URL is expired because the credits of my education account has been used up)
> > (will upload a video online for the website and give an URL)

---

## Software Architecture

![architecture](documentations/architecture.png)

---

## Use Case Examples: 

#### 1. Handwriting recognition + translation

​	choose "image" -> choose language -> upload image -> **get result !** 

![handwriting](documentations/handwriting.png)

#### 2. Irregular printing (cosmetics/logos)

​	choose "image" -> choose language -> upload image -> **get result !** 



![irregular](documentations/irregular.png)

#### 3. Video transcription

​	choose "video" -> login/sign up ( -> if sign up, then could confirm subscription) -> upload video -> wait until job completed -> if completed, then click to see transcription 

#### ![video](documentations/video.png)

#### 4. Transcription job tracking

 click "login" -> click "lists" -> choose completed job to see transcription

![track](documentations/track.png)

#### 5. Notification received in mailbox

​	in completed transcription page -> choose language -> click "confirm" -> receive email in mailbox

![notification](documentations/notification.png)

![email](documentations/email.png)

#### 6. Download translated file

​	in email with download link -> click on download link -> choose a position to save locally -> open txt file with any editor

![file](documentations/file.png)

---

## Screenshots

#### main page

> ![main](E:\Programming\webapp\Cloud-Computing\documentations\main.png)

#### login/signup (to use transcription feature)

> ![login](documentations/login.png)

> ![sign-up](documentations/sign-up.png)

> ##### 	validation
>
> > ![validation](documentations/validation.png)

#### image page

> ![image-page](documentations/image-page.png)

> ![sample results](documentations/sample results.png)

#### video page (create job)

> ![create job](documentations/create job.png)

#### job list

> ![empty list](documentations/empty list.png)

#### job detail

> ![job details](documentations/job details.png)