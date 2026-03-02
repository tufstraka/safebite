const fs = require('fs');

let content = fs.readFileSync('page.tsx', 'utf8');

// Replace safe_dishes.map with paginated version
content = content.replace(
  /results\.safe_dishes\.map\(\(dish: any, idx: number\)/g,
  'paginate(results.safe_dishes, safePage).items.map((dish: any, idx: number)'
);

// Add pagination controls after safe dishes
const safePagination = `
                {paginate(results.safe_dishes, safePage).totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-4">
                    <button
                      onClick={() => setSafePage(p => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-semibold disabled:opacity-50 hover:bg-emerald-600"
                    >
                      ← prev
                    </button>
                    <span className="text-gray-700 font-medium">
                      {safePage} / {paginate(results.safe_dishes, safePage).totalPages}
                    </span>
                    <button
                      onClick={() => setSafePage(p => Math.min(paginate(results.safe_dishes, safePage).totalPages, p + 1))}
                      disabled={safePage === paginate(results.safe_dishes, safePage).totalPages}
                      className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-semibold disabled:opacity-50 hover:bg-emerald-600"
                    >
                      next →
                    </button>
                  </div>
                )}`;

content = content.replace(
  /(\s+<\/div>\n\s+<\/div>\n\s+<\/div>\n\s+<\/div>\n\s+\)\}\n\n\s+{\/\* Unsafe \*\/})/,
  safePagination + '\n              </div>\n            </div>\n          )}\n\n            {/* Unsafe */'
);

// Do same for unsafe
content = content.replace(
  /results\.unsafe_dishes\.map\(\(dish: any, idx: number\)/g,
  'paginate(results.unsafe_dishes, unsafePage).items.map((dish: any, idx: number)'
);

const unsafePagination = `
                {paginate(results.unsafe_dishes, unsafePage).totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-4">
                    <button
                      onClick={() => setUnsafePage(p => Math.max(1, p - 1))}
                      disabled={unsafePage === 1}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg font-semibold disabled:opacity-50 hover:bg-red-600"
                    >
                      ← prev
                    </button>
                    <span className="text-gray-700 font-medium">
                      {unsafePage} / {paginate(results.unsafe_dishes, unsafePage).totalPages}
                    </span>
                    <button
                      onClick={() => setUnsafePage(p => Math.min(paginate(results.unsafe_dishes, unsafePage).totalPages, p + 1))}
                      disabled={unsafePage === paginate(results.unsafe_dishes, unsafePage).totalPages}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg font-semibold disabled:opacity-50 hover:bg-red-600"
                    >
                      next →
                    </button>
                  </div>
                )}`;

// Find the end of unsafe section
const unsafeEnd = content.match(/(<\/div>\n\s+<\/div>\n\s+\)\}\n\n\s+{\/\* Footer \*\/})/);
if (unsafeEnd) {
  content = content.replace(unsafeEnd[0], unsafePagination + '\n              </div>\n            </div>\n          )}\n\n        {/* Footer */}');
}

fs.writeFileSync('page.tsx', content);
console.log('✓ Added pagination controls');
