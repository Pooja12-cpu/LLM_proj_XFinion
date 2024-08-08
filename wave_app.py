from h2ogpte import H2OGPTE
from h2o_wave import main, app, Q, ui, data
import os

client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-X9MfyZWT1hKFEiNnRSbsnlizxo3kLVKb7RznESmVW6viMDvv',
)

llm_model = "OpenGVLab/InternVL-Chat-V1-5"

@app("/xfinion_llmbot")
async def serve(q: Q):
    q.page['card1'] = ui.form_card(box='1 1 11 1', items=[
        ui.text_xl(content='Xfinion DocBOT'),
    ])

    q.page['example'] = ui.form_card(box='6 2 3 3', items=[
    ui.file_upload(
        name='file_upload',
        label='File Upload',
        multiple=False,
        file_extensions=['pdf','txt'],
    )])

    if not q.client.initialized:
        q.page['card2'] = ui.chatbot_card(
            box='1 2 5 5',
            name='chatbot',
            data=data(fields='content from_user', t='list'),)
        q.client.initialized = True

    links = q.args.file_upload
    if links:
        items = [ui.text_xl('Files uploaded!')]
        for link in links:
            local_path = await q.site.download(link, '.')
            collection_id = client.create_collection( name='User', description='User input',)
            with open(local_path, 'rb') as f:
                doc1 = client.upload('UserDoc.txt',f)
                # Ingest documents (Creates previews, chunks and embeddings)
                client.ingest_uploads(collection_id, [doc1]) #The square brackets around 'doc1' are absolutely essential
        os.remove(local_path)
        q.page['example'].items = items

    if q.args.chatbot:
        #if collection_id != None:'
        name = "User"
        recent_collections = client.list_recent_collections(0, 1000)
        for c in recent_collections:
            if c.name == name and c.document_count:
                collection_id = c.id
                break
        q.page['card2'].data += [q.args.chatbot, True]
        chat_session_id = client.create_chat_session(collection_id)
        with client.connect(chat_session_id) as session:
            reply = session.query(q.args.chatbot, timeout=300, llm = llm_model)
            q.page['card2'].data += [reply.content, False]
        """else:
            q.page['card2'].items = [ui.text_l('Please upload a document')]   
            #size = os.path.getsize(local_path)"""
            #items.append(ui.link(label=f'{os.path.basename(link)} ({size} bytes)', download=True, path=link))
            # Clean up

        #items.append(ui.button(name='back', label='Back', primary=True))

    """if not q.client.initialized:
        q.page['card2'] = ui.chatbot_card(
            box='1 2 5 5',
            name='chatbot',
            data=data(fields='content from_user', t='list'),)
        q.client.initialized = True
    
    q.page['example'] = ui.form_card(box='6 2 3 3', items=[
    ui.file_upload(
        name='file_upload',
        label='File Upload',
        multiple=False,
        file_extensions=['pdf','txt'],
    )])

    if q.args.chatbot:
        q.page['card2'].data += [q.args.chatbot, True]

        links = q.args.flie_upload
        if links:
            items = [ui.text_xl('Files uploaded!')]
            for link in links:
                local_path = await q.site.download(link, '.')
                size = os.path.getsize(local_path)
            print(size)
            q.page['example'].items = items
        collection_id = client.create_collection( name='User', description='User input',)
        with open(local_path, 'rb') as f:
             doc1 = client.upload('UserDoc.txt',f)
             # Ingest documents (Creates previews, chunks and embeddings)
             client.ingest_uploads(collection_id, [doc1]) #The square brackets around 'doc1' are absolutely essential
        os.remove(local_path)
        chat_session_id = client.create_chat_session(collection_id)

        with client.connect(chat_session_id) as session:
            reply = session.query(q.args.chatbot, timeout=300, llm = llm_model)
        q.page['card2'].data += [size, False]"""

    await q.page.save()
