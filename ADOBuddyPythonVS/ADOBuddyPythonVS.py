import gradio as gr
import asyncio
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from mcp_use import MCPAgent, MCPClient
from langchain_openai import AzureChatOpenAI
from InstantDBScriptMaker import launch_db_script_maker
import threading

# Azure OpenAI Configuration


async def process_query(user_message):
    """Show all steps and stream logs from MCP tool execution."""
    try:
        # Step 1: Checking tools with npx
        yield "[Step 1/4] Checking tools with npx...\n"
        await asyncio.sleep(0.2)

        # MCP Configuration for Azure DevOps
        config = {
            "mcpServers": {
                "ado": {
                    "command": "npx",
                    "args": ["-y", "@azure-devops/mcp", "tr-tax"]
                }
            }
        }

        # Step 2: Creating MCPClient
        yield "[Step 2/4] Creating MCPClient...\n"
        await asyncio.sleep(0.2)
        client = MCPClient.from_dict(config)

        # Step 3: Getting user query and executing tools
        yield "[Step 3/4] Executing tools for your query...\n"
        await asyncio.sleep(0.2)
        llm = AzureChatOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
            azure_deployment=deployment,
            temperature=1.0,
            max_tokens=800
        )
        agent = MCPAgent(llm=llm, client=client, max_steps=30)

        # Patch: Ensure proper structure for work item creation
        patched_message = user_message
        if isinstance(user_message, dict):
            # If it looks like a work item creation request but missing fields
            if ("project" in user_message or "workItemType" in user_message) and "fields" not in user_message:
                patched_message = dict(user_message)  # shallow copy
                # If fields is missing, initialize it as empty dict
                if "fields" not in patched_message:
                    patched_message["fields"] = {}
            
            # For work item creation, also ensure we have the required structure
            if "project" in user_message and "workItemType" in user_message:
                # The MCP server might expect this structure for wit_create_work_item
                if not patched_message.get("fields"):
                    patched_message["fields"] = {}
                
                # Add any additional fields that might be at the root level to fields
                for key, value in list(patched_message.items()):
                    if key not in ["project", "workItemType", "fields"] and not key.startswith("System."):
                        # Move custom fields to the fields object
                        patched_message["fields"][key] = value
                        del patched_message[key]

        # Capture stdout/stderr during agent.run
        f = io.StringIO()
        e = io.StringIO()
        result = None
        try:
            with redirect_stdout(f), redirect_stderr(e):
                result = await agent.run(patched_message, max_steps=30)
        except Exception as ex:
            yield f"[Error during tool execution: {ex}]\n"
        # Stream captured logs
        logs = f.getvalue() + e.getvalue()
        if logs:
            for line in logs.splitlines():
                yield f"[log] {line}\n"
                await asyncio.sleep(0.01)

        # Step 4: Returning output
        yield "[Step 4/4] Returning output...\n"
        await asyncio.sleep(0.2)
        if result is not None:
            for char in str(result):
                yield char
                await asyncio.sleep(0.01)
        else:
            yield "[No output returned from tool.]\n"
    except Exception as e:
        yield f"Error: {str(e)}\n"

async def chatbot_response(message, history):
    """Gradio chatbot response function that handles streaming."""
    if not message.strip():
        history.append([message, "Please enter a message."])
        yield history
        return

    history.append([message, ""])
    
    try:
        async for chunk in process_query(message):
            history[-1][1] += chunk
            yield history
    except Exception as e:
        error_response = f"Error: {str(e)}"
        history[-1][1] = error_response
        yield history

def tool1():
    """Launch Instant DB Script Maker in a new tab"""
    try:
        # Launch in a separate thread to avoid blocking the main interface
        thread = threading.Thread(target=launch_db_script_maker, daemon=True)
        thread.start()
        return "Instant DB Script Maker launched in a new tab!"
    except Exception as e:
        return f"Error launching DB Script Maker: {str(e)}"

def tool2():
    return "Hello world 2"

# --- New CSS for the popup drawer ---
css = """
#tools-popup {
    position: fixed !important;
    top: 0;
    left: 0;
    height: 100%;
    width: 300px;
    background: white !important; /* Enforce white background */
    border-right: 1px solid #ddd;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease-in-out;
    padding: 20px;
    display: flex;
    flex-direction: column;
}
#tools-popup > .gr-column {
    background-color: transparent !important; /* Make column background transparent */
}
#tools-popup.visible {
    transform: translateX(0);
}
#tools-popup-overlay {
    position: fixed !important;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.4);
    z-index: 999;
    display: none; /* Handled by Gradio visibility */
}
#navbar-row {
    align-items: center;
}
#tools-hamburger-btn {
    font-size: 1.5em;
    padding: 10px;
    background: transparent;
    border: none;
    cursor: pointer;
    margin-right: 15px;
    color: #ff8c00; /* Set hamburger color to orange */
}
#close-popup-btn {
    position: absolute;
    top: 15px;
    right: 15px;
    background: transparent;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
}
"""

# Create Gradio interface with custom CSS
with gr.Blocks(title="Azure DevOps Chatbot", css=css) as demo:
    # State to manage popup visibility
    popup_visible = gr.State(False)

    # Navbar with hamburger button on the left
    with gr.Row(elem_id="navbar-row"):
        with gr.Column(scale=1, min_width=70):
            tools_hamburger_btn = gr.Button("☰", elem_id="tools-hamburger-btn")
        with gr.Column(scale=10):
            gr.Markdown(
                "<h1 style='text-align: center; margin: 0; padding: 20px; background: linear-gradient(90deg, #ff8c00, #ff7f00); color: white; border-radius: 8px;'>Smart Azure DevOps Assistant</h1>",
                elem_id="navbar"
            )

    # Popup overlay (to close the popup when clicked)
    tools_popup_overlay = gr.Button("", visible=False, elem_id="tools-popup-overlay")

    # Popup window (drawer) for tools, using gr.Group instead of gr.Box
    with gr.Group(visible=True, elem_id="tools-popup") as tools_popup:
        gr.Label("ADO Tools Suite")
        close_popup_btn = gr.Button("×", elem_id="close-popup-btn")
        with gr.Column():
            #gr.HTML("<div style='height: 20px;'></div>")# Spacer
            tool1_button = gr.Button("Instant DB Script Maker")
            #gr.HTML("<div style='height: 20px;'></div>")
            #tool2_button = gr.Button("Bulk SB creator")

    # Main chatbot interface
    with gr.Row():
        with gr.Column(scale=4):
            gr.Label("Azure DevOps Assistant Chatbot")
            chatbot = gr.Chatbot([], height=400)
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Enter your Azure DevOps query here...",
                    container=False,
                    scale=4
                )
                submit_btn = gr.Button("Submit", variant="primary", scale=1)
                clear = gr.Button("Clear", scale=1)
            gr.Markdown("<b><span style='color: red;'>Note: Chatbot functionality is limited to reading task data and updating specific fields. Task creation and deletion are restricted.</span></b>")
            gr.Examples(
                examples=[
                    "List me 1 task that I am assigned to in Azure DevOps in taxprof project",
                    "update comment as 'Unit testing completed' in task 4127687 in Taxprof project",
                    "Give me latest information on latest successful build pipeline of Roll BlueMoon Build Numbers in taxprof project"
                ],
                inputs=msg
            )

    # --- Event Handlers for Popup ---
    def toggle_popup(is_visible):
        return gr.update(visible=not is_visible), gr.update(visible=not is_visible)

    def close_popup():
        return gr.update(visible=False), gr.update(visible=False)

    tools_hamburger_btn.click(
        lambda: (gr.update(elem_classes="visible"), gr.update(visible=True)),
        outputs=[tools_popup, tools_popup_overlay]
    )

    close_popup_btn.click(
        lambda: (gr.update(elem_classes=""), gr.update(visible=False)),
        outputs=[tools_popup, tools_popup_overlay]
    )

    tools_popup_overlay.click(
        lambda: (gr.update(elem_classes=""), gr.update(visible=False)),
        outputs=[tools_popup, tools_popup_overlay]
    )

    # --- Original Event Handlers ---
    msg.submit(chatbot_response, [msg, chatbot], [chatbot])
    msg.submit(lambda: "", None, [msg])
    submit_btn.click(chatbot_response, [msg, chatbot], [chatbot])
    submit_btn.click(lambda: "", None, [msg])
    clear.click(lambda: [], None, [chatbot])
    tool1_button.click(tool1, outputs=msg)

if __name__ == "__main__":
    print("Starting Azure DevOps Chatbot...")
    demo.launch(
        server_name="127.0.0.3",
        server_port=7880,
        share=False,
        show_error=True,
        inbrowser=True
    )
