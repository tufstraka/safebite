const fs = require('fs');

let content = fs.readFileSync('page.tsx', 'utf8');

// Add reasoning boxes to safe dishes
content = content.replace(
  /<p className="text-gray-600 text-sm mb-2">{dish\.description}<\/p>\n\s+<p className="text-gray-700 text-sm font-medium italic">{dish\.recommendations}<\/p>/g,
  `<p className="text-gray-600 text-sm mb-2">{dish.description}</p>
                      {dish.safe_explanation && (
                        <div className="bg-emerald-100 rounded-lg p-3 mb-2 border border-emerald-300">
                          <p className="text-emerald-800 text-sm font-medium">
                            <span className="font-bold">why it works:</span> {dish.safe_explanation}
                          </p>
                        </div>
                      )}
                      <p className="text-gray-700 text-sm font-medium italic">{dish.recommendations}</p>`
);

// Add reasoning boxes to unsafe dishes (find the second occurrence)
const unsafeMatch = content.match(/(<div key={idx} className="p-6 rounded-2xl shadow-sm bg-gray-100 border border-red-900">[\s\S]*?)<p className="text-red-700 text-sm font-semibold">{dish\.recommendations}<\/p>/);
if (unsafeMatch) {
  const unsafeSection = unsafeMatch[0];
  const updated = unsafeSection.replace(
    /<p className="text-red-700 text-sm font-semibold">{dish\.recommendations}<\/p>/,
    `{dish.reasoning && (
                        <div className="bg-red-100 rounded-lg p-3 mb-2 border border-red-300">
                          <p className="text-red-800 text-sm font-medium">
                            <span className="font-bold">why to skip:</span> {dish.reasoning}
                          </p>
                        </div>
                      )}
                      <p className="text-red-700 text-sm font-semibold">{dish.recommendations}</p>`
  );
  content = content.replace(unsafeMatch[0], updated);
}

fs.writeFileSync('page.tsx', content);
console.log('✓ Added reasoning boxes');
