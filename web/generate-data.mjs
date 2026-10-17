import { mkdir, writeFile, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dataDirectory = join(here, "data");
const detailsDirectory = join(here, "details");

const categories = ["Audio", "Dom inteligentny", "Fotografia", "Komputery", "Kuchnia", "Mobilność", "Ogród", "Zdrowie"];
const brands = ["Aster", "Błękit", "Coda", "Dąb", "Elektra", "Fokus", "Żar & Córka", "Horyzont"];
const adjectives = ["Miejski", "Profesjonalny", "Kompaktowy", "Cichy", "Precyzyjny", "Ekologiczny", "Przenośny", "Nowoczesny"];
const nouns = ["głośnik", "ekspres", "monitor", "odkurzacz", "zegarek", "router", "aparat", "projektor"];
const colors = ["grafitowy", "srebrny", "zielony", "kremowy", "granatowy", "czerwony", "czarny", "biały"];
const materials = ["aluminium", "stal nierdzewna", "tworzywo ABS", "szkło hartowane", "bambus", "poliwęglan"];
const countries = ["Polska", "Czechy", "Niemcy", "Japonia", "Szwecja", "Włochy"];

function pricePresentation(value, index) {
  const currency = ["zł", "EUR", "USD"][index % 3];
  const [whole, decimals] = value.toFixed(2).split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
  if (currency === "zł") return { currency, display: `${grouped},${decimals} zł` };
  if (currency === "EUR") return { currency, display: `${grouped},${decimals} EUR` };
  return { currency, display: `${grouped}.${decimals} USD` };
}

function makeProduct(index) {
  const id = String(index).padStart(4, "0");
  const priceValue = Number((49.9 + ((index * 97) % 4300) + (index % 9) * 0.37).toFixed(2));
  const price = pricePresentation(priceValue, index);
  const category = index % 6 === 0 ? null : categories[index % categories.length];
  const availability = index % 6 === 1 ? null : ["Dostępny", "Ostatnie sztuki", "Wysyłka w 24 h", "Na zamówienie"][index % 4];
  const brand = index % 17 === 0 ? null : brands[index % brands.length];
  const date = new Date(Date.UTC(2026, (index * 3) % 10, (index % 27) + 1));
  const dateAdded = date.toISOString().slice(0, 10);
  return {
    id,
    page: Math.ceil(index / 80),
    display_type: index % 2 === 0 ? "table" : "card",
    warehouse: ["WAW-1", "KRK-2", "GDN-3", "POZ-4"][index % 4],
    name: `${adjectives[index % adjectives.length]} ${nouns[index % nouns.length]} ${id}`,
    price_value: priceValue,
    price_display: price.display,
    currency: price.currency,
    category,
    brand,
    availability,
    rating: Number((3.4 + ((index * 13) % 17) / 10).toFixed(1)),
    reviews_count: (index * 31) % 970,
    date_added: dateAdded,
    warranty_months: index % 10 === 0 ? null : [12, 24, 36][index % 3],
    model: `NV-${categories[index % categories.length].slice(0, 3).toUpperCase()}-${id}`,
    energy_class: ["A", "B", "C", "D"][index % 4],
    shipping_days: (index % 5) + 1,
    seller: `Nova Partner ${((index - 1) % 12) + 1}`,
    ean: `590${String(1000000000 + index).slice(-10)}`,
    weight: `${(0.2 + (index % 47) / 10).toFixed(1)} kg`,
    dimensions: `${20 + (index % 31)} × ${12 + (index % 23)} × ${5 + (index % 16)} cm`,
    color: index % 8 === 0 ? null : colors[index % colors.length],
    country_of_origin: countries[index % countries.length],
    material: materials[index % materials.length],
    condition: index % 13 === 0 ? "Powystawowy" : "Nowy",
    description: `Model ${id} łączy funkcjonalność i trwałość. Dane demonstracyjne zawierają polskie znaki: ą, ć, ę, ł, ń, ó, ś, ź, ż.`
  };
}

function detailPage(product) {
  const value = (field) => product[field] ?? "";
  return `<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${product.name} — Nova Market</title><link rel="stylesheet" href="../css/details.css"></head>
<body><main class="detail"><a class="back-link" href="../../mock.html">← Wróć do katalogu</a><p class="eyebrow">NOVA MARKET / SPECYFIKACJA</p><h1>${product.name}</h1><p class="lead">${product.price_display} · ${value("availability") || "brak danych o dostępności"}</p><section class="product-specs"><h2>Parametry techniczne</h2><dl><div><dt>EAN</dt><dd id="spec-ean">${product.ean}</dd></div><div><dt>Waga</dt><dd id="spec-weight">${product.weight}</dd></div><div><dt>Wymiary</dt><dd id="spec-dims">${product.dimensions}</dd></div><div><dt>Kolor</dt><dd id="spec-color">${value("color")}</dd></div><div><dt>Kraj pochodzenia</dt><dd id="spec-origin">${product.country_of_origin}</dd></div><div><dt>Materiał</dt><dd id="spec-material">${product.material}</dd></div><div><dt>Stan</dt><dd id="spec-condition">${product.condition}</dd></div><div><dt>Model</dt><dd id="spec-model">${product.model}</dd></div><div><dt>Klasa energetyczna</dt><dd id="spec-energy-class">${product.energy_class}</dd></div><div><dt>Dostawa</dt><dd id="spec-shipping-days">${product.shipping_days} dni</dd></div></dl><details id="spec-details"><summary>Opis produktu</summary><p class="description-text">${product.description}</p></details></section></main></body></html>`;
}

const uniqueProducts = Array.from({ length: 400 }, (_, offset) => makeProduct(offset + 1));
const duplicateProducts = uniqueProducts.slice(0, 12).map((product, index) => ({ ...product, page: ((product.page + index) % 5) + 1, duplicate_of: product.id }));
const products = [...uniqueProducts, ...duplicateProducts];

await mkdir(dataDirectory, { recursive: true });
await rm(detailsDirectory, { recursive: true, force: true });
await mkdir(detailsDirectory, { recursive: true });
await writeFile(join(dataDirectory, "products.json"), `${JSON.stringify(products, null, 2)}\n`, "utf8");
await Promise.all(uniqueProducts.map((product) => writeFile(join(detailsDirectory, `product-${product.id}.html`), detailPage(product), "utf8")));
console.log(`Utworzono ${products.length} wpisów katalogu (${uniqueProducts.length} unikalnych) i ${uniqueProducts.length} stron szczegółów.`);
