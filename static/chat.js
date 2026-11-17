// Chat page logic. Replies are added with textContent (never innerHTML), so nothing the AI
// or a user types can inject HTML or scripts into the page.
const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const history = [];   // last few turns, sent with each question so follow-ups make sense

function addMessage(text, who) {
    const div = document.createElement("div");
    div.className = `msg ${who}`;
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
}

async function ask(question) {
    addMessage(question, "user");
    const typing = addMessage("…", "bot typing");
    send.disabled = true;
    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: question, history: history.slice(-6)}),
        });
        const data = await res.json();
        typing.remove();
        const reply = data.reply || data.error || "Sorry, something went wrong.";
        addMessage(reply, "bot");
        history.push({role: "user", text: question}, {role: "assistant", text: reply});
    } catch {
        typing.remove();
        addMessage("Sorry, I couldn't connect. Please check your internet and try again.", "bot");
    } finally {
        send.disabled = false;
        input.focus();
    }
}

form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    document.getElementById("suggestions").hidden = true;
    ask(q);
});

document.querySelectorAll("#suggestions button").forEach((b) =>
    b.addEventListener("click", () => {
        document.getElementById("suggestions").hidden = true;
        ask(b.textContent);
    })
);
