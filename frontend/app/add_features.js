const fs = require('fs');

const content = fs.readFileSync('page.tsx', 'utf8');

// 1. Add pagination state after existing state
const stateAddition = `  const [scanHistory, setScanHistory] = useState<any[]>([]);

  // Pagination state
  const [safePage, setSafePage] = useState(1);
  const [unsafePage, setUnsafePage] = useState(1);
  const [unknownPage, setUnknownPage] = useState(1);
  const ITEMS_PER_PAGE = 10;`;

let newContent = content.replace(
  '  const [scanHistory, setScanHistory] = useState<any[]>([]);',
  stateAddition
);

// 2. Add pagination helper function after state
const paginateHelper = `
  // Pagination helper
  const paginate = (items: any[], page: number) => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    return {
      items: items.slice(start, end),
      totalPages: Math.ceil(items.length / ITEMS_PER_PAGE),
      currentPage: page
    };
  };
`;

newContent = newContent.replace(
  '  const loadHistory = () => {',
  paginateHelper + '\n  const loadHistory = () => {'
);

// 3. Add recommendation section after stats
const recommendationSection = `
            {/* AI Recommendation */}
            {results.recommendation && (
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 mb-6 border-2 border-purple-400 shadow-sm">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✨</span>
                  <div className="flex-1">
                    <h3 className="text-lg font-black text-purple-900 mb-2">recommended for you</h3>
                    <p className="text-purple-800 font-medium">{results.recommendation}</p>
                  </div>
                </div>
              </div>
            )}
`;

newContent = newContent.replace(
  '            {/* Safe */}\n            {results.safe_dishes.length > 0 && (',
  recommendationSection + '\n            {/* Safe */}\n            {results.safe_dishes.length > 0 && ('
);

fs.writeFileSync('page.tsx', newContent);
console.log('✓ Added pagination state and recommendation section');
