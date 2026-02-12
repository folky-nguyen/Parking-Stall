const form = document.querySelector("#pc-form");
const list = document.querySelector("#pc-list");
const stats = document.querySelector("#stats");
const searchInput = document.querySelector("#search");
const template = document.querySelector("#pc-item-template");
const formMessage = document.querySelector("#form-message");

let pcs = [];
let query = "";

bootstrap();

async function bootstrap() {
  await loadPcs();
  render();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFormMessage();

  const data = new FormData(form);
  const name = String(data.get("name") || "").trim();
  const cpu = String(data.get("cpu") || "").trim();
  const purpose = String(data.get("purpose") || "").trim();
  const note = String(data.get("note") || "").trim();

  const ram = parsePositiveInt(data.get("ram"));
  const storage = parsePositiveInt(data.get("storage"));

  if (!name || !cpu || !purpose) {
    setFormMessage("Vui lòng nhập đầy đủ Tên máy, CPU và Mục đích.");
    return;
  }

  if (!ram || !storage) {
    setFormMessage("RAM và Ổ cứng phải là số nguyên dương.");
    return;
  }

  const item = {
    id: crypto.randomUUID(),
    name,
    cpu,
    ram,
    storage,
    purpose,
    note,
  };

  try {
    const response = await fetch("/api/pcs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "Không thể lưu dữ liệu.");
    }

    pcs.unshift(payload);
    form.reset();
    setFormMessage("Đã lưu cấu hình vào database thành công.", true);
    render();
  } catch (error) {
    setFormMessage(error.message || "Đã có lỗi xảy ra khi lưu dữ liệu.");
  }
});

searchInput.addEventListener("input", (event) => {
  query = event.target.value.trim().toLowerCase();
  render();
});

list.addEventListener("click", async (event) => {
  const button = event.target.closest(".delete-btn");
  if (!button) {
    return;
  }

  const id = button.dataset.id;
  if (!id) {
    return;
  }

  try {
    const response = await fetch(`/api/pcs/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.message || "Không thể xóa dữ liệu.");
    }

    pcs = pcs.filter((pc) => pc.id !== id);
    render();
  } catch (error) {
    setFormMessage(error.message || "Đã có lỗi khi xóa dữ liệu.");
  }
});

async function loadPcs() {
  try {
    const response = await fetch("/api/pcs");
    const payload = await response.json();

    if (!response.ok || !Array.isArray(payload)) {
      throw new Error("Không thể tải dữ liệu từ database.");
    }

    pcs = payload;
  } catch (error) {
    pcs = [];
    setFormMessage(error.message || "Không thể tải dữ liệu từ database.");
  }
}

function parsePositiveInt(value) {
  const raw = String(value || "").trim();
  if (!/^\d+$/.test(raw)) {
    return 0;
  }

  const number = Number.parseInt(raw, 10);
  return number > 0 ? number : 0;
}

function setFormMessage(message, isSuccess = false) {
  formMessage.textContent = message;
  formMessage.classList.toggle("success", isSuccess);
}

function clearFormMessage() {
  formMessage.textContent = "";
  formMessage.classList.remove("success");
}

function render() {
  const filtered = pcs.filter((pc) => {
    if (!query) return true;
    const content = `${pc.name} ${pc.cpu} ${pc.purpose} ${pc.note}`.toLowerCase();
    return content.includes(query);
  });

  list.innerHTML = "";

  if (!filtered.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = pcs.length
      ? "Không tìm thấy cấu hình phù hợp."
      : "Chưa có dữ liệu. Hãy thêm máy đầu tiên của bạn.";
    list.appendChild(empty);
  }

  filtered.forEach((pc) => {
    const node = template.content.cloneNode(true);
    node.querySelector(".pc-name").textContent = pc.name;
    node.querySelector(".pc-spec").textContent = `CPU: ${pc.cpu} • RAM: ${pc.ram}GB • SSD/HDD: ${pc.storage}GB`;
    node.querySelector(".pc-purpose").textContent = `Mục đích: ${pc.purpose}`;
    node.querySelector(".pc-note").textContent = pc.note || "Không có ghi chú.";
    node.querySelector(".delete-btn").dataset.id = pc.id;
    list.appendChild(node);
  });

  const totalRam = pcs.reduce((sum, item) => sum + item.ram, 0);
  const totalStorage = pcs.reduce((sum, item) => sum + item.storage, 0);
  stats.textContent = `Tổng máy: ${pcs.length} • Tổng RAM: ${totalRam}GB • Tổng dung lượng lưu trữ: ${totalStorage}GB`;
}
