import streamlit as st
import google.generativeai as genai
import json
import os
import time

USERS = ["Adeel", "Anubhav", "Andrew"]
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "jokes.json")
AVATARS = {
    "Adeel": os.path.join(APP_DIR, "Adeel.png"),
    "Anubhav": os.path.join(APP_DIR, "anubhav.png"),
    "Andrew": os.path.join(APP_DIR, "Andrew.png"),
}


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"jokes": []}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def generate_joke(target, topic):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Write a short, funny Yo Momma joke about {topic}. The target is {target}."
    response = model.generate_content(prompt)
    return response.text.strip()


def login_page():
    st.title("Yo Momma Sharks :shark:")
    st.subheader("Pick your fighter")
    name = st.selectbox("Who are you?", USERS)
    st.image(AVATARS[name], width=200, caption=name)
    if st.button("Login"):
        st.session_state.user = name
        st.rerun()

    st.divider()
    st.subheader("How to Play")
    st.markdown(
        """
1. **Login** by selecting your name above.
2. **Pick a target** — choose one of the other two players to roast.
3. **Enter a topic** (e.g. "Bad Driver") and hit **Generate Roast** (or press Enter).
4. The AI will craft a Yo Momma joke aimed at your target.
5. **Voting rules:**
   - The **sender** and **target** cannot vote on a joke.
   - Only the **third party** (the uninvolved player) can upvote or downvote.
   - Each player can only vote once per joke.
6. **Scoreboard** tracks each player's total score (upvotes minus downvotes).
7. The player with the highest score is the ultimate **Yo Momma Shark**!
"""
    )


def main_page():
    user = st.session_state.user
    db = load_db()

    st.title("Yo Momma Sharks :shark:")
    st.caption(f"Logged in as **{user}**")
    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

    # --- Scoreboard ---
    st.header("Scoreboard")
    scores = {u: 0 for u in USERS}
    for joke in db["jokes"]:
        scores[joke["sender"]] += joke["upvotes"] - joke["downvotes"]
    cols = st.columns(3)
    for i, u in enumerate(USERS):
        with cols[i]:
            st.metric(u, scores[u])

    st.divider()

    # --- Roast Arena ---
    st.header("The Roast Arena")
    targets = [u for u in USERS if u != user]

    with st.form("roast_form"):
        col_target, col_topic = st.columns(2)
        with col_target:
            target = st.selectbox("Choose your target", targets)
        with col_topic:
            topic = st.text_input("Topic (e.g. 'Bad Driver')")
        submitted = st.form_submit_button("Generate Roast", type="primary")

    if submitted:
        if not topic.strip():
            st.warning("Enter a topic first!")
        else:
            st.toast("Generating roast...", icon="🦈")
            with st.spinner("Cooking up a roast..."):
                joke_text = generate_joke(target, topic.strip())
            joke_entry = {
                "id": int(time.time() * 1000),
                "sender": user,
                "target": target,
                "topic": topic.strip(),
                "content": joke_text,
                "upvotes": 0,
                "downvotes": 0,
                "voted_by": [],
            }
            db["jokes"].append(joke_entry)
            save_db(db)
            st.toast("Roast generated!", icon="🔥")
            time.sleep(3)
            st.rerun()

    st.divider()

    # --- Feed ---
    st.header("Joke Feed")
    if not db["jokes"]:
        st.info("No jokes yet. Be the first to roast!")
        return

    for joke in reversed(db["jokes"]):
        with st.container(border=True):
            st.markdown(f"**{joke['sender']}** roasted **{joke['target']}** on *{joke['topic']}*")
            st.write(joke["content"])
            score = joke["upvotes"] - joke["downvotes"]
            st.caption(f"Score: {score} | Upvotes: {joke['upvotes']} | Downvotes: {joke['downvotes']}")

            is_sender = user == joke["sender"]
            is_target = user == joke["target"]
            has_voted = user in joke.get("voted_by", [])

            if not is_sender and not is_target:
                if has_voted:
                    st.caption("You already voted on this one.")
                else:
                    c1, c2, _ = st.columns([1, 1, 4])
                    with c1:
                        if st.button("Upvote", key=f"up_{joke['id']}"):
                            joke["upvotes"] += 1
                            joke.setdefault("voted_by", []).append(user)
                            save_db(db)
                            st.rerun()
                    with c2:
                        if st.button("Downvote", key=f"down_{joke['id']}"):
                            joke["downvotes"] += 1
                            joke.setdefault("voted_by", []).append(user)
                            save_db(db)
                            st.rerun()


if "user" not in st.session_state:
    login_page()
else:
    main_page()
