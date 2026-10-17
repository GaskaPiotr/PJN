const pageNumber = Number(document.body.dataset.catalogPage);
const batchSize = 20;
let catalog = [];
let visibleProducts = [];
let cursor = 0;

const tableBody = document.querySelector("#products-table tbody");
const cards = document.querySelector("#products-container");
const loadMore = document.querySelector("#load-more");
const status = document.querySelector("#catalog-status");
const search = document.querySelector("#search-input");
const category = document.querySelector("#category-filter");
const sort = document.querySelector("#sort-select");

const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'\"]/g, (character) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", "\"":"&quot;" })[character]);
const textOrEmpty = (value) => value ? escapeHtml(value) : "";

function orderedCardFields(product) {
  const fields = [
    ["cat", "Kategoria", product.category], ["brand", "Marka", product.brand],
    ["stock", "Dostępność", product.availability], ["rating", "Ocena", product.rating],
    ["reviews", "Opinie", product.reviews_count], ["date", "Dodano", product.date_added],
    ["warranty", "Gwarancja", product.warranty_months ? `${product.warranty_months} mies.` : null],
    ["model", "Model", product.model], ["energy-class", "Klasa energ.", product.energy_class]
  ];
  return fields.sort(() => Math.random() - 0.5);
}

function renderProduct(product, index) {
  const link = `web/details/product-${product.id}.html`;
  const row = document.createElement("tr");
  row.className = "product-row";
  row.dataset.id = product.id;
  row.dataset.warehouse = product.warehouse;
  row.innerHTML = `<td class="name">${escapeHtml(product.name)}</td><td class="price">${escapeHtml(product.price_display)}</td><td class="cat">${textOrEmpty(product.category)}</td><td class="brand">${textOrEmpty(product.brand)}</td><td class="stock">${textOrEmpty(product.availability)}</td><td class="rating">${escapeHtml(product.rating)}</td><td class="reviews">${escapeHtml(product.reviews_count)}</td><td class="date">${escapeHtml(product.date_added)}</td><td class="warranty">${product.warranty_months ? `${product.warranty_months} mies.` : ""}</td><td><a class="details-link" href="${link}">Szczegóły</a></td>`;

  const card = document.createElement("article");
  card.className = "product-card";
  card.dataset.id = product.id;
  card.dataset.warehouse = product.warehouse;
  const metadata = orderedCardFields(product).map(([className, label, value]) => value ? `<span class="${className}"><strong>${label}:</strong> ${textOrEmpty(value)}</span>` : "").join("");
  card.innerHTML = `<p class="pill">Magazyn ${escapeHtml(product.warehouse)}</p><h3 class="name">${escapeHtml(product.name)}</h3><p class="price">${escapeHtml(product.price_display)}</p><div class="meta">${metadata}</div><a class="details-link" href="${link}">Zobacz specyfikację →</a>`;
  if (product.display_type === "table") {
    tableBody.append(row);
  } else {
    cards.append(card);
  }
}

async function loadBatch() {
  loadMore.disabled = true;
  const delay = Math.floor(Math.random() * 1701) + 300;
  status.textContent = `Pobieranie następnej porcji danych (${(delay / 1000).toFixed(2)} s)…`;
  await wait(delay);
  const batch = visibleProducts.slice(cursor, cursor + batchSize);
  batch.forEach(renderProduct);
  cursor += batch.length;
  status.textContent = `Wyświetlono ${cursor} z ${visibleProducts.length} produktów na stronie ${pageNumber}.`;
  if (cursor >= visibleProducts.length) {
    loadMore.hidden = true;
  } else {
    loadMore.disabled = false;
  }
}

function applyFilters() {
  const query = search.value.trim().toLocaleLowerCase("pl");
  const selectedCategory = category.value;
  visibleProducts = catalog.filter((product) => (!query || product.name.toLocaleLowerCase("pl").includes(query)) && (!selectedCategory || product.category === selectedCategory));
  if (sort.value === "price-asc") visibleProducts.sort((a, b) => a.price_value - b.price_value);
  if (sort.value === "price-desc") visibleProducts.sort((a, b) => b.price_value - a.price_value);
  if (sort.value === "rating-desc") visibleProducts.sort((a, b) => b.rating - a.rating);
  tableBody.replaceChildren();
  cards.replaceChildren();
  cursor = 0;
  loadMore.hidden = false;
  loadBatch();
}

async function initialise() {
  try {
    const response = await fetch("web/data/products.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const products = await response.json();
    catalog = products.filter((product) => product.page === pageNumber);
    [...new Set(catalog.map((product) => product.category).filter(Boolean))].sort().forEach((name) => category.add(new Option(name, name)));
    [search, category, sort].forEach((control) => control.addEventListener("input", applyFilters));
    visibleProducts = [...catalog];
    await loadBatch();
  } catch (error) {
    status.textContent = "Nie udało się pobrać katalogu. Uruchom stronę przez serwer HTTP.";
    loadMore.hidden = true;
    console.error(error);
  }
}

loadMore.addEventListener("click", loadBatch);
initialise();
