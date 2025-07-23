fetch("/api/schedules")
  .then(res => res.json())
  .then(data => {
    const ul = document.getElementById("schedule-list");
    data.forEach((item, index) => {
      const li = document.createElement("li");
      li.textContent = `${item.date} ${item.start}〜${item.end}：${item.title}`;
      ul.appendChild(li);
    });
  });
