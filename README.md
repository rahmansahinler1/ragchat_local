**# ragchat local**

ragchat is a chatbot that enables you to intreact with your personal files. 
It automatically updates it's own vector database. Filling domain folder with related documents will be enough.
You can interact with you data with just chatting. RAG Chat effortlessly obtain the most up-to-date information for you with the resource of information.
If you come across any bug please insert an issue for us or you can mail the problem rahmansahinler1@gmail.com
Also, if you like some of the feature please also send an e-mail about it.

**# To get started**
1) Select latest release branch. Example: feature/v0.1
2) Clone to branch into your environment
3) Install the necessary libraries. I highly suggest using virtual environments
	- python --> 3.12
	- libraries --> requirements.txt
	- API Key --> Insert one openai api key under ".env" file with OPENAI_API_KEY = "your api key"

! ragchat can be used within both windows and mac environments.

You can start using it with running ragchat.bat file

![sample-usecase](https://github.com/user-attachments/assets/071a8e4b-2479-4376-bb5c-a8d1d91be4d4)

**# User Guide**

To use raghcat just following these rules are enough!

1) Insert your pdf documents under given domain folders
2) In first running main.py they will be created for you. You can view them under db/domains
3) Fill the domain folder with pdfs you want to interact
! Domains must be related with each other. You will be interacting with them. Fill them carefully, something like research papers on anomaly detection or legal documentation on retail business might be suitable.
4) You can select your domain with the button in the upper right hand side file icon.
5) ragchat will be detecting file changes everytime you open it. When you manually change files while using it, in this button there is another button with run file detection. Click it, ragchat will be updating it's memory.
