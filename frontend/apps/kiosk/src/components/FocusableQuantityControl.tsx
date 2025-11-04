
// FocusableQuantityControl.tsx
import { FunctionComponent, useState, useEffect, useCallback, useRef } from "react";

export type FocusableQuantityControlProps = {
  className?: string;
  initialQuantity?: number;
  onQuantityChange?: (quantity: number) => void;
  onFocusChange?: (isFocused: boolean) => void;
  itemName?: string;
};

/**
 * A focusable quantity control component that demonstrates the "focus" concept.
 * When focused, it responds to keyboard input (+ and - keys) and highlights
 * the available actions to the user.
 */
const FocusableQuantityControl: FunctionComponent<FocusableQuantityControlProps> = ({
  className = "",
  initialQuantity = 1,
  onQuantityChange,
  onFocusChange,
  itemName = "Item"
}) => {
  const [quantity, setQuantity] = useState(initialQuantity);
  const [isFocused, setIsFocused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle quantity changes
  const handleQuantityChange = useCallback((newQuantity: number) => {
    if (newQuantity >= 0) {
      setQuantity(newQuantity);
      onQuantityChange?.(newQuantity);
    }
  }, [onQuantityChange]);

  // Handle focus state changes
  const handleFocusChange = useCallback((focused: boolean) => {
    setIsFocused(focused);
    onFocusChange?.(focused);
  }, [onFocusChange]);

  // Keyboard event handler for focused state
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!isFocused) return;

    switch (event.key) {
      case '+':
      case '=': // Plus key without shift
        event.preventDefault();
        handleQuantityChange(quantity + 1);
        break;
      case '-':
      case '_': // Minus key
        event.preventDefault();
        handleQuantityChange(quantity - 1);
        break;
      case 'Escape':
        event.preventDefault();
        handleFocusChange(false);
        containerRef.current?.blur();
        break;
    }
  }, [isFocused, quantity, handleQuantityChange, handleFocusChange]);

  // Set up keyboard event listeners
  useEffect(() => {
    if (isFocused) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isFocused, handleKeyDown]);

  // Handle mouse/touch interactions
  const handleIncrement = () => handleQuantityChange(quantity + 1);
  const handleDecrement = () => handleQuantityChange(quantity - 1);

  // Handle focus events
  const handleFocus = () => handleFocusChange(true);
  const handleBlur = () => handleFocusChange(false);

  return (
    <div
      ref={containerRef}
      className={`
        relative flex items-center gap-2 p-2 rounded-lg transition-all duration-200
        ${isFocused 
          ? 'bg-blue-100 border-2 border-blue-500 shadow-lg' 
          : 'bg-gray-100 border-2 border-transparent hover:border-gray-300'
        }
        ${className}
      `}
      tabIndex={0}
      onFocus={handleFocus}
      onBlur={handleBlur}
      role="spinbutton"
      aria-label={`Quantity control for ${itemName}`}
      aria-valuenow={quantity}
      aria-valuemin={0}
    >
      {/* Focus indicator and instructions */}
      {isFocused && (
