// File: src/components/CategoryItem.tsx
import { FunctionComponent, useMemo, type CSSProperties } from "react";

export type CategoryItemType = {
  className?: string;
  categoryItemText?: string;
  categoryName?: string;
  isActive?: boolean;
  onHover?: (categoryName: string) => void;
  onClick?: (categoryName: string) => void;
  disableInteraction?: boolean;

  /** Variant props */
  property1?: string;

  /** Style props */
  categoryItemWidth?: CSSProperties["width"];
};

const CategoryItem: FunctionComponent<CategoryItemType> = ({
  className = "",
  categoryItemWidth,
  categoryItemText,
  categoryName,
  isActive = false,
  onHover,
  onClick,
  disableInteraction = false,
}) => {
  const categoryItemStyle: CSSProperties = useMemo(() => {
    return {
      width: categoryItemWidth,
    };
  }, [categoryItemWidth]);

  const handleMouseEnter = () => {
    if (!disableInteraction && onHover && categoryName) {
      onHover(categoryName);
    }
  };

  const handleClick = () => {
    if (!disableInteraction && onClick && categoryName) {
      onClick(categoryName);
    }
  };

  // Dynamic styling based on active state
  const textColor = isActive ? 'text-[#fff]' : 'text-[#a7a7a7]';
  const backgroundColor = isActive ? 'bg-[#ff0000]' : 'bg-transparent';
  const cursorStyle = (!disableInteraction && (onHover || onClick)) ? 'cursor-pointer' : '';

  return (
    <div
      className={`flex items-center justify-start py-[0.312rem] px-[0rem] box-border text-left text-[1.625rem] font-['PT_Sans'] ${backgroundColor} ${cursorStyle} ${className}`}
      style={categoryItemStyle}
      onMouseEnter={handleMouseEnter}
      onClick={handleClick}
    >
      <h2 className={`m-0 text-[length:inherit] font-medium font-[inherit] whitespace-nowrap ${textColor}`}>
        {categoryItemText}
      </h2>
    </div>
  );
};

export default CategoryItem;
