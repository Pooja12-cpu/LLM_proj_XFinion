from h2ogpte import H2OGPTE
from h2o_wave import main, app, Q, ui, data
import os
import datetime

"""Setting up the h2ogpte connection with the Python client API key"""
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='XXXXXXXXXXXXXXXXXXXXXXXXXX', #Enter your API key within the quotes
)

llm_model = "meta-llama/Meta-Llama-3.1-8B-Instruct" #After analysis, it was concluded that this is 
#by far the best model to be used in addition to 'gpt-4-1106-preview’ 

d1 = ["Files Uploaded:"] #Initializing a list of strings to store the names of the files uploaded


@app("/xfinion_llmbot") #This determines the web-address of the application
async def serve(q: Q):

    """This function is based off of the app function of H2O. It is a basic function that forms
    the backbone of any H2O wave web application. It takes in a query argument (q) which represents 
    the query context and is updated every time a query arrives from the browser."""

    collection_id = None #Intializing the collection_id for the h2ogpte based collection as None. 

    """A collection in h2ogpte is an empty set for documents. Usually each collection in h2ogpte
    has its own API key and collection ID. When documents are uploaded in the backend to H2O, this
    a collection must be created to store the documents to.
    
    The same collection can however be accessed later programmatically using just its name."""

    q.page['card1'] = ui.form_card(box='1 1 11 1',items=[
        ui.text_xl(content="Xfinion DocBOT")
    ]) #Creating a header card to display the title of the application

    q.page['file_upload'] = ui.form_card(box='6 2 3 3', items=[
    ui.file_upload(
        name='file_upload',
        label='File Upload',
        multiple=False,
        file_extensions=['pdf','txt'],
    )]) #Creating a card to upload files with restricted file types. Here it is pdf or txt.

    q.page['card3'] = ui.form_card(box='6 5 3 3', items=[
        ui.text_xl(content='Files Uploaded:'),
    ]) #Creating a card to display the list of files uploaded so far by the user

    if not q.client.initialized: #If the client is not initialzed, a chatbot card is created
        q.page['card2'] = ui.chatbot_card(
            box='1 2 5 5',
            name='chatbot',
            data=data(fields='content from_user', t='list'),)
        q.client.initialized = True

    links = q.args.file_upload #Creating a variable to track the uploaded files
    name = "User" #Intializing name of user collection in h2ogpte

    """The for loop below helps us ensure that the documents of the current user are all stored in 
    the same collection. To do this, it iterates over the list of collections to find if a collection 
    with the same name exits before proceeding. If it does, the collection ID is stored into the collection_id
    variable."""
    recent_collections = client.list_recent_collections(0, 1000)
    for c in recent_collections:
        if c.name == name and c.document_count:
            collection_id = c.id
            break

    if links: #If user has uploaded files, the code below is executed 
        items = [ui.text_xl('Files uploaded! Please reload page to add more files')] #Items are a list of 
        #new texts/buttons/cards that are to be displayed when the user interacts with the application
        for link in links: 
            local_path = await q.site.download(link, '.') #Downloading the file uploaded by user
            d1.append(os.path.basename(link)) #Appending the name of the file to the list initialized earlier
            with open(local_path, 'rb') as f:
                doc1 = client.upload(os.path.basename(link),f) #Uploading the file onto h2ogpte
                # Ingest documents (Creates previews, chunks and embeddings)
                if collection_id!=None: #If the collection was already created we simply proceed to ingest 
                    #the documents within it
                    client.ingest_uploads(collection_id, [doc1]) 
                else: #Else, a new collection with the same name is created
                    collection_id = client.create_collection( name='User', description='User input',)
                    client.ingest_uploads(collection_id, [doc1])
        os.remove(local_path) #Deleting the downloaded file once its uploaded to h2ogpte
        q.page['file_upload'].items = items #Updating the list of items on the 'File Upload' card

    """Initializing a new items list for the card that displays the files uploaded"""
    items2 = [ui.text_l(f'{d1[0]}\n')] #Displaying the first element of the files uploaded list
    if len(d1)>1: #If files have been uploaded, displaying them one below the other
        for i in range(1,len(d1)):
            items2.append(ui.text(f'{d1[i]}\n'))
    q.page['card3'].items = items2

    """If user starts a chat the following code is executed"""
    if q.args.chatbot:
        name = "User"
        recent_collections = client.list_recent_collections(0, 1000)
        for c in recent_collections:
            if c.name == name and c.document_count:
                collection_id = c.id
                break
        q.page['card2'].data += [q.args.chatbot, True] #Displaying user entered content in the card first
        chat_session_id = client.create_chat_session(collection_id) #Starting a chat session with the same
        #collection ID as before
        with client.connect(chat_session_id) as session:
            reply = session.query(q.args.chatbot, timeout=300, llm = llm_model) #Fetching the LLM's reply 
            #for the given question
            q.page['card2'].data += [reply.content, False] #Displaying the model's reply

    await q.page.save() #Saving all changes so far
