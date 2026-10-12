"""
Ashiee Native Desktop GUI Application
Built with CustomTkinter for a classic Antigravity desktop pair-programming experience.
"""

import asyncio
import threading
import webbrowser
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from ashiee.config import AshieeConfig
from ashiee.core.agent import AshieeAgent, AgentEvent


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AshieeDesktopGUI(ctk.CTk):
    def __init__(self, config: AshieeConfig = None):
        super().__init__()
        self.config = config or AshieeConfig()
        self.agent = AshieeAgent(self.config)

        self.title("Ashiee — Google Antigravity Studio")
        self.geometry("1180x760")
        self.minsize(960, 600)
        self.configure(fg_color="#0b0d14")

        self._setup_event_listeners()
        self._build_layout()

    def _setup_event_listeners(self):
        def on_event(event_type: str, data: dict):
            if event_type == AgentEvent.THOUGHT:
                self.after(0, self._append_thought, data.get("thought", ""))
            elif event_type == AgentEvent.TOOL_START:
                self.after(0, self._append_tool_card, data.get("name", ""), "executing...")
            elif event_type == AgentEvent.TOOL_END:
                status = "✔ Completed" if data.get("success") else "✖ Failed"
                self.after(0, self._append_tool_card, data.get("name", ""), status, data.get("output", ""))
            elif event_type == AgentEvent.ERROR:
                self.after(0, self._append_message, "System", f"Error: {data.get('error')}", "#ef4444")

        self.agent.add_event_listener(on_event)

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#121522")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="✦ Ashiee Antigravity",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#4285f4"
        )
        self.logo_label.pack(padx=16, pady=(20, 4), anchor="w")

        self.sub_label = ctk.CTkLabel(
            self.sidebar,
            text="AI-First Pair Programmer",
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        )
        self.sub_label.pack(padx=16, pady=(0, 16), anchor="w")

        # New Chat Button
        self.btn_new = ctk.CTkButton(
            self.sidebar,
            text="+ New Chat",
            fg_color="#1c2438",
            hover_color="#27324d",
            command=self._clear_chat,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_new.pack(padx=14, pady=8, fill="x")

        # Workspace Box
        self.lbl_ws = ctk.CTkLabel(self.sidebar, text="WORKSPACE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b")
        self.lbl_ws.pack(padx=16, pady=(16, 4), anchor="w")

        ws_name = Path(self.config.workspace_root).name
        self.lbl_ws_val = ctk.CTkLabel(self.sidebar, text=f"📁 {ws_name}", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        self.lbl_ws_val.pack(padx=16, pady=2, anchor="w")

        # Model Target
        self.lbl_model = ctk.CTkLabel(self.sidebar, text="MODEL TARGET", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b")
        self.lbl_model.pack(padx=16, pady=(16, 4), anchor="w")
        self.lbl_model_val = ctk.CTkLabel(self.sidebar, text="✦ Gemini 3.8 Flash (High)", font=ctk.CTkFont(size=12), text_color="#c084fc")
        self.lbl_model_val.pack(padx=16, pady=2, anchor="w")

        # Live Project Portal Button
        self.btn_live = ctk.CTkButton(
            self.sidebar,
            text="🌐 Live Portal (Port 5000)",
            fg_color="#0f5132",
            hover_color="#198754",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_live_portal
        )
        self.btn_live.pack(padx=14, pady=(20, 4), fill="x")

        # Status Dot
        self.status_bar = ctk.CTkLabel(self.sidebar, text="● Engine Online", font=ctk.CTkFont(size=11), text_color="#10b981")
        self.status_bar.pack(side="bottom", padx=16, pady=16, anchor="w")

        # 2. Main Chat Area
        self.chat_container = ctk.CTkFrame(self, fg_color="#0b0d14", corner_radius=0)
        self.chat_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.chat_container.grid_rowconfigure(0, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)

        # Messages Scrollable Frame
        self.messages_frame = ctk.CTkScrollableFrame(self.chat_container, fg_color="#0b0d14")
        self.messages_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        # Bottom Input Area
        self.input_frame = ctk.CTkFrame(self.chat_container, fg_color="#121522", corner_radius=12, border_width=1, border_color="#202538")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry_prompt = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Message Ashiee (e.g., 'Build a login system for my website')...",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=0,
            height=40
        )
        self.entry_prompt.grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        self.entry_prompt.bind("<Return>", lambda e: self._send_prompt())

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=70,
            height=32,
            fg_color="#4285f4",
            hover_color="#3367d6",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._send_prompt
        )
        self.btn_send.grid(row=0, column=1, padx=10, pady=8)

        # 3. Right Auxiliary Pane (Thoughts & Terminal)
        self.aux_pane = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#121522")
        self.aux_pane.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)
        self.aux_pane.grid_propagate(False)

        self.lbl_aux = ctk.CTkLabel(self.aux_pane, text="REASONING STREAM", font=ctk.CTkFont(size=11, weight="bold"), text_color="#c084fc")
        self.lbl_aux.pack(padx=14, pady=(16, 6), anchor="w")

        self.thought_box = ctk.CTkTextbox(self.aux_pane, fg_color="#0e111c", text_color="#d8b4fe", font=ctk.CTkFont(size=11), wrap="word")
        self.thought_box.pack(padx=14, pady=6, fill="both", expand=True)

        self.lbl_term = ctk.CTkLabel(self.aux_pane, text="TERMINAL OUTPUT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10b981")
        self.lbl_term.pack(padx=14, pady=(12, 6), anchor="w")

        self.term_box = ctk.CTkTextbox(self.aux_pane, fg_color="#080a10", text_color="#34d399", font=ctk.CTkFont(family="Consolas", size=10), wrap="none", height=180)
        self.term_box.pack(padx=14, pady=(0, 16), fill="x")

        # Welcome Card
        self._append_message("Ashiee", "Hello! I am Ashiee, your Antigravity-integrated pair programmer.\nAsk me to explore files, build code, or run tests!", "#4285f4")

    def _append_message(self, sender: str, text: str, color: str = "#4285f4"):
        bubble = ctk.CTkFrame(self.messages_frame, fg_color="#161a2a" if sender == "Ashiee" else "#1c2538", corner_radius=10)
        bubble.pack(fill="x", padx=10, pady=6, anchor="w" if sender == "Ashiee" else "e")

        header = ctk.CTkLabel(bubble, text=sender, font=ctk.CTkFont(size=11, weight="bold"), text_color=color)
        header.pack(anchor="w", padx=12, pady=(8, 2))

        msg = ctk.CTkLabel(bubble, text=text, font=ctk.CTkFont(size=13), text_color="#f8fafc", justify="left", wraplength=540)
        msg.pack(anchor="w", padx=12, pady=(2, 10))

    def _append_thought(self, thought_text: str):
        self.thought_box.insert("end", f"✦ {thought_text}\n\n")
        self.thought_box.see("end")

    def _append_tool_card(self, tool_name: str, status: str, output: str = ""):
        card = ctk.CTkFrame(self.messages_frame, fg_color="#0f1422", border_width=1, border_color="#283754", corner_radius=6)
        card.pack(fill="x", padx=10, pady=3)

        txt = f"⚙ Tool: {tool_name} — {status}"
        lbl = ctk.CTkLabel(card, text=txt, font=ctk.CTkFont(family="Consolas", size=11), text_color="#38bdf8")
        lbl.pack(padx=10, pady=6, anchor="w")

        if output:
            self.term_box.insert("end", f"[$] {tool_name}\n{output}\n\n")
            self.term_box.see("end")

    def _clear_chat(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.thought_box.delete("1.0", "end")
        self.term_box.delete("1.0", "end")
        self._append_message("Ashiee", "Session cleared. Ready for your instructions!", "#4285f4")

    def _send_prompt(self):
        prompt = self.entry_prompt.get().strip()
        if not prompt:
            return

        self._append_message("You", prompt, "#94a3b8")
        self.entry_prompt.delete(0, "end")
        self.btn_send.configure(state="disabled")

        # Run turn in background thread
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.agent.execute_turn(prompt))
            self.after(0, self._on_turn_finished, response)

        threading.Thread(target=_run, daemon=True).start()

    def _on_turn_finished(self, response: str):
        self._append_message("Ashiee", response, "#4285f4")
        self.btn_send.configure(state="normal")

    def _open_live_portal(self):
        webbrowser.open("http://127.0.0.1:5000")


def launch_gui():
    app = AshieeDesktopGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
