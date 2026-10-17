const $ = (id) => document.getElementById(id);
const fmt = (n) => (n === null || n === undefined ? "hidden" : Number(n).toLocaleString());
const LABELS = { positive: "Positive", neutral: "Neutral", negative: "Negative" };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function fillList(id, items, emptyText) {
  const list = $(id);
  list.replaceChildren();
  (items.length ? items : [emptyText]).forEach((item) => list.append(el("li", items.length ? "" : "muted", item)));
}

function showStatus(text, kind) {
  const status = $("status");
  status.textContent = text;
  status.className = "status" + (kind ? " " + kind : "");
  status.hidden = !text;
}

function render(data) {
  const v = data.video;
  $("thumb").src = v.Thumbnail || "";
  $("thumb").hidden = !v.Thumbnail;
  $("title").textContent = v.Title;
  $("channel").textContent = v.Channel_name + " · " + new Date(v.Published_date).toLocaleDateString();
  $("views").textContent = fmt(v.Views);
  $("likes").textContent = fmt(v.Likes);
  $("ncomments").textContent = fmt(v.Comment_count);
  $("analyzed").textContent = fmt(data.comments_analyzed);

  // Sentiment bar
  const bar = $("bar"), legend = $("legend");
  bar.replaceChildren(); legend.replaceChildren();
  const p = data.sentiment_percents, c = data.sentiment_counts;
  bar.setAttribute("aria-label", Object.keys(LABELS).map((k) => `${LABELS[k]} ${p[k]}%`).join(", "));
  for (const key of Object.keys(LABELS)) {
    const seg = el("div", "seg " + key);
    seg.style.width = p[key] + "%";
    if (p[key] >= 8) seg.textContent = Math.round(p[key]) + "%";
    bar.append(seg);
    const item = el("span", "legend-item");
    item.append(el("i", "dot " + key), `${LABELS[key]} ${p[key]}% (${c[key]})`);
    legend.append(item);
  }

  // Example comments
  const examples = $("examples");
  examples.replaceChildren();
  for (const key of Object.keys(LABELS)) {
    const col = el("div");
    col.append(el("h4", key === "positive" ? "pos" : key === "negative" ? "neg" : "", LABELS[key]));
    const list = data.examples[key];
    if (!list.length) col.append(el("p", "muted", "None"));
    list.forEach((cm) => {
      const q = el("blockquote", "", cm.Text);
      q.append(el("small", "", `👍 ${fmt(cm.Likes)}`));
      col.append(q);
    });
    examples.append(col);
  }

  const a = data.analysis;
  $("verdict-card").hidden = !a;
  $("ai").hidden = !a;
  $("analysis-error").hidden = !data.analysis_error;
  $("analysis-error").textContent = data.analysis_error || "";

  if (a) {
    $("score").textContent = a.score;
    $("verdict").textContent = a.verdict;
    $("verdict-card").dataset.tone = a.score >= 7 ? "good" : a.score <= 4 ? "bad" : "mixed";
    $("headline").textContent = a.headline;
    $("summary").textContent = a.summary;
    $("interpretation").textContent = a.interpretation;
    fillList("liked", a.what_people_liked, "Nothing stood out");
    fillList("disliked", a.what_people_disliked, "No real complaints");
    fillList("questions", a.questions_and_confusion, "None");

    const themes = $("themes");
    themes.replaceChildren();
    a.themes.forEach((t) => {
      const box = el("div", "theme");
      const head = el("div", "theme-head");
      head.append(el("strong", "", t.name), el("span", "tag " + t.sentiment, t.sentiment));
      box.append(head, el("p", "", t.description), el("blockquote", "", t.example_quote));
      themes.append(box);
    });

    const notable = $("notable");
    notable.replaceChildren();
    a.notable_comments.forEach((n) => {
      const q = el("blockquote", "", n.text);
      q.append(el("small", "", n.why_it_matters));
      notable.append(q);
    });
  }

  $("results").hidden = false;
}

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("go");
  button.disabled = true;
  $("results").hidden = true;
  showStatus("Fetching comments and analysing… this can take up to a minute.");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: $("url").value }),
    });
    const data = await res.json().catch(() => ({ error: "The server returned an unexpected response." }));
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    showStatus("");
    render(data);
  } catch (err) {
    showStatus(err.message, "error");
  } finally {
    button.disabled = false;
  }
});
