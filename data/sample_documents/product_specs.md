# E-Shop Product Specifications

## Discount Codes

- **SAVE15**: Applies 15% discount on total order
- **SAVE20**: Applies 20% discount on total order (valid only for orders above $100)
- **FLAT50**: Applies flat $50 discount (valid only for orders above $200)
- Invalid codes should display error: "Invalid discount code"
- Only one discount code can be applied per order

## Shipping Rules

- **Standard Shipping**: Free, 5-7 business days
- **Express Shipping**: $10, 2-3 business days
- Free express shipping for orders above $500

## Pricing and Tax

- All prices include base price
- Tax is calculated at 10% of subtotal (after discount)
- Final Total = (Subtotal - Discount) + Tax + Shipping

## Payment Methods

- Credit Card: Requires card number, expiry, CVV
- PayPal: Redirects to PayPal
- Cash on Delivery: Available for orders below $300

## Validation Rules

- Minimum order amount: $50
- Email must be valid format
- All required fields must be filled
- Terms and conditions must be accepted

## Product Inventory

1. Smartphone - $699
2. Laptop - $1299
3. Headphones - $199
4. Smartwatch - $399
5. Tablet - $499

## Business Logic

### Cart Functionality

- Users can add products to cart
- Cart displays product name, price, quantity, and thumbnail
- Quantity can be increased or decreased using +/- buttons
- Items can be removed from cart
- Cart total updates in real-time
- Empty cart displays message: "Your cart is empty. Start shopping!"

### Discount Code Validation

- Discount codes must be entered in the discount code input field
- Clicking "Apply" button validates the code
- Valid codes display success message in GREEN: "Discount applied: [code] - [amount]"
- Invalid codes display error in RED: "Invalid discount code"
- Discount codes have minimum order requirements:
  - SAVE15: No minimum
  - SAVE20: $100 minimum
  - FLAT50: $200 minimum
- If minimum not met, display error: "Minimum order amount of $[amount] required for this code"

### Order Calculation

1. Subtotal: Sum of all cart items (price × quantity)
2. Discount: Applied based on valid discount code
3. Tax: 10% of (Subtotal - Discount)
4. Shipping: Based on selected method
5. Final Total: Subtotal - Discount + Tax + Shipping

### Form Validation

- **Name field**: Required, must not be empty
  - Error: "⚠ Full Name is required"
- **Email field**: Required, must be valid email format
  - Error: "⚠ Invalid email format"
- **Terms checkbox**: Must be checked
  - Error: "⚠ You must accept terms and conditions"
- Valid fields show GREEN border
- Invalid fields show RED border
- Validation occurs on blur (when user leaves field)

### Checkout Process

1. Verify cart is not empty
2. Verify minimum order amount ($50)
3. Validate all required form fields
4. Check payment method restrictions (COD only for orders < $300)
5. Display loading spinner during processing
6. Show success message upon completion
7. Reset form after successful order

## Error Messages

### Cart Errors

- "Your cart is empty" - when trying to checkout with empty cart
- "Minimum order amount is $50" - when cart total < $50

### Discount Errors

- "Please enter a discount code" - when apply button clicked with empty field
- "Invalid discount code" - when code not found in system
- "Minimum order amount of $[X] required for this code" - when order doesn't meet minimum

### Form Errors

- "⚠ Full Name is required" - empty name field
- "⚠ Invalid email format" - invalid email
- "⚠ You must accept terms and conditions" - terms not checked

### Payment Errors

- "Cash on Delivery is only available for orders below $300" - COD selected for order ≥ $300

## UI Behavior

### Button States

- **Add to Cart buttons**: BLUE (#3B82F6), changes to darker blue on hover
- **Apply Discount button**: BLUE (#3B82F6)
- **Pay Now button**: GREEN (#10B981), changes to darker green on hover
- **Disabled Pay Now button**: GRAY with reduced opacity, not clickable
- **Loading state**: Shows spinner icon with "Processing..." text

### Color Codes

- Success messages: GREEN (#10B981)
- Error messages: RED (#EF4444)
- Primary action buttons: GREEN (#10B981)
- Secondary action buttons: BLUE (#3B82F6)
- Disabled states: GRAY

### Cart Badge

- Shows total number of items in cart
- Displayed on cart icon in header
- Updates in real-time when items added/removed
- Red background (#EF4444) with white text

## Accessibility Requirements

- All form inputs have associated labels
- Error messages are clearly visible and descriptive
- Buttons have descriptive text
- Color contrast ratio meets WCAG standards (minimum 4.5:1)
- Form validation provides clear feedback

## Responsive Design

- Maximum width: 1200px
- Layout adapts for mobile devices
- Products grid: 2 columns on desktop, 1 column on mobile
- Cart section: Sticky on desktop, scrollable on mobile
