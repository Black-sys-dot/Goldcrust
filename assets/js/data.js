/* ==========================================================================
   GOLDCRUST — static menu data
   Frontend only. This module is the single source of truth for the UI until
   a real API exists; swapping it for fetch() calls later should be a drop-in.
   ========================================================================== */

const CATEGORIES = [
  { id: 'all',      name: 'All',        emoji: '✨' },
  { id: 'chicken',  name: 'Fried Chicken', emoji: '🍗' },
  { id: 'burgers',  name: 'Burgers',    emoji: '🍔' },
  { id: 'wraps',    name: 'Wraps & Bowls', emoji: '🌯' },
  { id: 'sides',    name: 'Sides',      emoji: '🍟' },
  { id: 'combos',   name: 'Combos',     emoji: '🍱' },
  { id: 'desserts', name: 'Desserts',   emoji: '🍰' },
  { id: 'drinks',   name: 'Drinks',     emoji: '🥤' },
];

/* tags: bestseller | new | spicy | veg */
const MENU = [
  /* ---------------------------------------------------------- chicken --- */
  {
    id: 'ch-01', name: 'Golden Crunch Bucket', category: 'chicken', emoji: '🍗',
    price: 649, mrp: 749, rating: 5, likes: '243K', kcal: 1180, time: 25,
    tags: ['bestseller'],
    desc: '8 pieces of our signature hand-breaded chicken, double-dipped and fried till the crust sings.',
  },
  {
    id: 'ch-02', name: 'Fiery Peri Peri Wings', category: 'chicken', emoji: '🍗', accent: '🌶️',
    price: 269, rating: 5, likes: '198K', kcal: 540, time: 18,
    tags: ['spicy', 'bestseller'],
    desc: 'Six wings tossed in African bird\'s eye chilli rub with a squeeze of lime.',
  },
  {
    id: 'ch-03', name: 'Classic Crispy Strips', category: 'chicken', emoji: '🍖',
    price: 239, rating: 4, likes: '120K', kcal: 470, time: 15,
    tags: [],
    desc: 'Five tender fillet strips with a choice of dip. The safe order that never disappoints.',
  },
  {
    id: 'ch-04', name: 'Smoky BBQ Drumsticks', category: 'chicken', emoji: '🍗', accent: '🔥',
    price: 299, rating: 4, likes: '86K', kcal: 620, time: 22,
    tags: [],
    desc: 'Four drumsticks glazed in molasses BBQ, finished over open flame.',
  },
  {
    id: 'ch-05', name: 'Nashville Hot Chicken', category: 'chicken', emoji: '🍗', accent: '🌶️',
    price: 279, rating: 5, likes: '61K', kcal: 700, time: 20,
    tags: ['spicy', 'new'],
    desc: 'Three pieces bathed in cayenne butter, served on toast with house pickles.',
  },
  {
    id: 'ch-06', name: 'Grilled Herb Chicken', category: 'chicken', emoji: '🍗', accent: '🌿',
    price: 319, rating: 4, likes: '44K', kcal: 390, time: 24,
    tags: [],
    desc: 'Four flame-grilled pieces marinated in rosemary, garlic and lemon. No breading.',
  },

  /* ---------------------------------------------------------- burgers --- */
  {
    id: 'bg-01', name: 'Crust Signature Zinger', category: 'burgers', emoji: '🍔', accent: '🌶️',
    price: 199, mrp: 229, rating: 5, likes: '312K', kcal: 610, time: 12,
    tags: ['bestseller', 'spicy'],
    desc: 'The one that built the chain. Crunchy fillet, jalapeño mayo, iceberg, brioche.',
  },
  {
    id: 'bg-02', name: 'Double Down Deluxe', category: 'burgers', emoji: '🍔', accent: '🥓',
    price: 289, rating: 4, likes: '97K', kcal: 890, time: 14,
    tags: [],
    desc: 'Two fillets, smoked cheddar, bacon crumble and burnt-garlic aioli.',
  },
  {
    id: 'bg-03', name: 'Smoky Cheese Melt', category: 'burgers', emoji: '🍔', accent: '🧀',
    price: 219, rating: 4, likes: '73K', kcal: 640, time: 12,
    tags: [],
    desc: 'Molten cheddar blanket over a crispy patty with caramelised onion jam.',
  },
  {
    id: 'bg-04', name: 'Paneer Tikka Burger', category: 'burgers', emoji: '🍔', accent: '🧆',
    price: 179, rating: 4, likes: '88K', kcal: 520, time: 11,
    tags: ['veg'],
    desc: 'Charred tandoori paneer slab, mint chutney and crunchy onion.',
  },
  {
    id: 'bg-05', name: 'Crispy Veggie Supreme', category: 'burgers', emoji: '🍔', accent: '🥬',
    price: 159, rating: 4, likes: '52K', kcal: 480, time: 10,
    tags: ['veg'],
    desc: 'Corn and potato patty, herbed mayo, double lettuce, toasted sesame bun.',
  },
  {
    id: 'bg-06', name: 'Nashville Hot Burger', category: 'burgers', emoji: '🍔', accent: '🌶️',
    price: 229, rating: 5, likes: '35K', kcal: 700, time: 13,
    tags: ['new', 'spicy'],
    desc: 'Cayenne-lacquered fillet, comeback sauce and crunchy slaw. Handle with care.',
  },

  /* ------------------------------------------------------ wraps/bowls --- */
  {
    id: 'wr-01', name: 'Chicken Longer Wrap', category: 'wraps', emoji: '🌯',
    price: 149, rating: 4, likes: '141K', kcal: 430, time: 10,
    tags: ['bestseller'],
    desc: 'A full-length strip rolled with crunchy veg and chipotle mayo.',
  },
  {
    id: 'wr-02', name: 'Peri Peri Rice Bowl', category: 'wraps', emoji: '🍚', accent: '🌶️',
    price: 229, rating: 5, likes: '78K', kcal: 560, time: 16,
    tags: ['spicy'],
    desc: 'Herbed rice, grilled peri chicken, charred corn and a citrus drizzle.',
  },
  {
    id: 'wr-03', name: 'Paneer Kathi Wrap', category: 'wraps', emoji: '🌯',
    price: 139, rating: 4, likes: '46K', kcal: 410, time: 10,
    tags: ['veg'],
    desc: 'Flaky paratha, spiced paneer, pickled onion and green chutney.',
  },
  {
    id: 'wr-04', name: 'Loaded Chicken Bowl', category: 'wraps', emoji: '🍲', accent: '🧀',
    price: 259, rating: 4, likes: '39K', kcal: 620, time: 15,
    tags: ['new'],
    desc: 'Popcorn chicken over mash and gravy, topped with cheese and jalapeño.',
  },

  /* ------------------------------------------------------------ sides --- */
  {
    id: 'sd-01', name: 'Golden Fries', category: 'sides', emoji: '🍟',
    price: 99, rating: 5, likes: '402K', kcal: 320, time: 7,
    tags: ['bestseller', 'veg'],
    desc: 'Skin-on, twice-fried, salted the second they leave the basket.',
  },
  {
    id: 'sd-02', name: 'Peri Peri Loaded Fries', category: 'sides', emoji: '🍟', accent: '🌶️',
    price: 149, rating: 5, likes: '186K', kcal: 480, time: 9,
    tags: ['spicy', 'veg'],
    desc: 'Fries buried under cheese sauce, peri dust and spring onion.',
  },
  {
    id: 'sd-03', name: 'Crispy Popcorn Chicken', category: 'sides', emoji: '🍿',
    price: 169, rating: 5, likes: '224K', kcal: 420, time: 10,
    tags: ['bestseller'],
    desc: 'Bite-sized, impossibly crunchy, dangerously easy to finish alone.',
  },
  {
    id: 'sd-04', name: 'Cheesy Garlic Bread', category: 'sides', emoji: '🥖',
    price: 129, rating: 4, likes: '64K', kcal: 380, time: 9,
    tags: ['veg'],
    desc: 'Buttered sourdough, roasted garlic and a mozzarella lid.',
  },
  {
    id: 'sd-05', name: 'Onion Rings', category: 'sides', emoji: '🧅',
    price: 119, rating: 4, likes: '58K', kcal: 340, time: 8,
    tags: ['veg'],
    desc: 'Thick-cut rings in a beer-style batter with smoky dip.',
  },
  {
    id: 'sd-06', name: 'Coleslaw Bucket', category: 'sides', emoji: '🥗',
    price: 89, rating: 4, likes: '31K', kcal: 180, time: 5,
    tags: ['veg'],
    desc: 'Cold, creamy, sharp with vinegar. The counterweight to everything fried.',
  },

  /* ----------------------------------------------------------- combos --- */
  {
    id: 'cb-01', name: 'Solo Feast Combo', category: 'combos', emoji: '🍱',
    price: 349, mrp: 419, rating: 5, likes: '156K', kcal: 980, time: 20,
    tags: ['bestseller'],
    desc: '2 pc chicken, a Zinger, regular fries and a chilled drink.',
  },
  {
    id: 'cb-02', name: 'Duo Date Box', category: 'combos', emoji: '🍱',
    price: 599, mrp: 719, rating: 4, likes: '82K', kcal: 1840, time: 25,
    tags: [],
    desc: '4 pc chicken, 2 burgers, 2 fries and 2 drinks. Built for two.',
  },
  {
    id: 'cb-03', name: 'Family Festive Bucket', category: 'combos', emoji: '🍗', accent: '🎉',
    price: 999, mrp: 1249, rating: 5, likes: '211K', kcal: 3400, time: 30,
    tags: ['bestseller'],
    desc: '8 pc chicken, 4 wraps, large fries, popcorn chicken and 4 drinks.',
  },
  {
    id: 'cb-04', name: 'Midnight Munchies Box', category: 'combos', emoji: '🍱', accent: '🌙',
    price: 449, rating: 4, likes: '67K', kcal: 1240, time: 22,
    tags: ['new'],
    desc: 'Wings, popcorn chicken, loaded fries and a thick shake. 10pm onwards.',
  },

  /* --------------------------------------------------------- desserts --- */
  {
    id: 'ds-01', name: 'Choco Lava Cake', category: 'desserts', emoji: '🍰',
    price: 99, rating: 5, likes: '174K', kcal: 310, time: 8,
    tags: ['bestseller', 'veg'],
    desc: 'Warm cocoa sponge with a molten centre that actually flows.',
  },
  {
    id: 'ds-02', name: 'Vanilla Soft Swirl', category: 'desserts', emoji: '🍦',
    price: 69, rating: 4, likes: '92K', kcal: 210, time: 5,
    tags: ['veg'],
    desc: 'Classic soft serve in a crisp cone. Add chocolate dip if you must.',
  },
  {
    id: 'ds-03', name: 'Gulab Jamun Duo', category: 'desserts', emoji: '🍮',
    price: 89, rating: 4, likes: '48K', kcal: 290, time: 6,
    tags: ['veg'],
    desc: 'Two warm khoya dumplings soaked in cardamom syrup.',
  },

  /* ----------------------------------------------------------- drinks --- */
  {
    id: 'dr-01', name: 'Choco Thick Shake', category: 'drinks', emoji: '🥤', accent: '🍫',
    price: 149, rating: 5, likes: '133K', kcal: 420, time: 6,
    tags: ['bestseller', 'veg'],
    desc: 'Spoon-standing thick, real cocoa, whipped cream on top.',
  },
  {
    id: 'dr-02', name: 'Iced Lemon Tea', category: 'drinks', emoji: '🧋',
    price: 99, rating: 4, likes: '57K', kcal: 120, time: 4,
    tags: ['veg'],
    desc: 'Black tea over ice with fresh lemon and a mint sprig.',
  },
  {
    id: 'dr-03', name: 'Chilled Cola', category: 'drinks', emoji: '🥤',
    price: 89, rating: 4, likes: '210K', kcal: 180, time: 3,
    tags: ['veg'],
    desc: 'Large, over-iced, exactly as cold as it should be.',
  },
];

/* Per-item customisation offered in the detail sheet. Prices are deltas. */
const OPTION_GROUPS = {
  size: {
    label: 'Choose size',
    required: true,
    choices: [
      { id: 'regular', name: 'Regular', delta: 0 },
      { id: 'large',   name: 'Large',   delta: 60 },
      { id: 'sharing', name: 'Sharing', delta: 140 },
    ],
  },
  spice: {
    label: 'Spice level',
    required: true,
    choices: [
      { id: 'mild',   name: 'Mild',        delta: 0 },
      { id: 'medium', name: 'Medium',      delta: 0 },
      { id: 'hot',    name: 'Fiery hot',   delta: 20 },
    ],
  },
  addons: {
    label: 'Add extras',
    multi: true,
    choices: [
      { id: 'cheese', name: 'Extra cheese slice', delta: 35 },
      { id: 'dip',    name: 'Signature dip',      delta: 25 },
      { id: 'fries',  name: 'Upgrade to fries',   delta: 60 },
      { id: 'drink',  name: 'Add a chilled cola', delta: 55 },
    ],
  },
};

const FEES = { delivery: 39, packaging: 20, taxRate: 0.05, freeDeliveryOver: 599 };

const OFFERS = [
  { code: 'CRUST50',  title: '50% off up to ₹120', sub: 'On your first three orders', emoji: '🎁' },
  { code: 'BUCKET99', title: 'Bucket at ₹99 off',  sub: 'Min order ₹599 · Today only', emoji: '🍗' },
  { code: 'FREEDEL',  title: 'Free delivery',      sub: 'Orders above ₹599',           emoji: '🛵' },
];
