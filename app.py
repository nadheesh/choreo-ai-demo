import gradio as gr


def echo(text, request: gr.Request):
    if request:
        print("Request headers dictionary:", request.headers)
        print("IP address:", request.client.host)
        print("Query parameters:", dict(request.query_params))
    return text


interface = gr.Interface(echo, "textbox", "textbox")
interface.launch(server_name="0.0.0.0", server_port=9000)
