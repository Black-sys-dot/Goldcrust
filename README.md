# Goldcrust (Bytebite) 🍗✨

A fast, responsive food delivery web application featuring a clean user interface and a lightweight Python backend. The project includes a static frontend with a fully functional shopping cart and a FastAPI backend to handle the checkout process.

## Features

- **Interactive Menu**: Browse through categories like Fried Chicken, Burgers, Wraps, Sides, Desserts, and Drinks.
- **Advanced Filtering**: Filter by category, sort by price/rating/popularity, and toggle vegetarian options.
- **Persistent Cart**: The shopping cart uses `localStorage` to save your items even if you refresh or close the tab.
- **Customization**: Choose portion sizes, spice levels, and add extras directly from the item details view.
- **Checkout Flow**: Complete the checkout process with a simulated API integration handled by a Python backend.
- **Responsive Design**: Carefully crafted for both desktop and mobile web experiences without relying on heavy frameworks.

## Tech Stack

- **Frontend**: Vanilla HTML5, CSS3, and JavaScript. No build steps or heavy frameworks required.
- **Backend**: Python 3 with [FastAPI](https://fastapi.tiangolo.com/) and Uvicorn.
- **Architecture**: The frontend is served statically by the backend, which also exposes an API endpoint (`/api/checkout`) to process orders.

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

- Python 3.8+ 

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Black-sys-dot/Bytebite.git
   cd Bytebite
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**
   ```bash
   pip install fastapi uvicorn
   ```

### Running the Application

1. **Start the FastAPI server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the web application**
   Open your browser and navigate to `http://localhost:8000`.

3. **View backend orders (Admin)**
   You can view the list of placed orders by navigating to `http://localhost:8000/api/orders`.

## Project Structure

- `index.html` - The landing page with offers and features.
- `menu.html` - The full menu browsing and filtering page.
- `checkout.html` - The final checkout and order placement screen.
- `main.py` - The FastAPI backend application.
- `assets/` - Contains static assets:
  - `css/styles.css` - Custom styling.
  - `js/app.js` - Core application logic, cart state, and UI handlers.
  - `js/data.js` - Static dataset for menu items, categories, and offers.

## License

This project is open-source and available for educational purposes and customization.
