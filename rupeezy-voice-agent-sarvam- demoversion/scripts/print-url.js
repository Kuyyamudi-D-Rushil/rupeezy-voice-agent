const [, , label, url] = process.argv;

if (!label || !url) {
  process.exit(0);
}

console.log("");
console.log(`${label} URL: ${url}`);
console.log("");
