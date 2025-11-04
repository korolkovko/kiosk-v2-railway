// File: src/components/ItemList.tsx
import { FunctionComponent } from "react";
import { useKioskNavigation } from "../hooks/useKioskNavigation";

export type ItemListType = {
  className?: string;
  disableInteraction?: boolean;
};

const ItemList: FunctionComponent<ItemListType> = ({
  className = "",
  disableInteraction = false
}) => {
  const {
    currentCategoryItems,
    navigationMode,
    handleItemHover,
    isItemActive,
    activeItemIndex: _activeItemIndex
  } = useKioskNavigation();

  // Only show hover effects when in items navigation mode and not disabled
  const showItemHover = navigationMode === 'items' && !disableInteraction;

  return (
    <div
      className={`h-[67.5rem] bg-[#000] overflow-hidden flex flex-col items-start pt-[2.5rem] px-[0.625rem] pb-[0.625rem] box-border max-w-full text-left text-[1.625rem] text-[#fff] font-['PT_Sans'] mq450:pt-[1.625rem] mq450:pb-[1.25rem] mq450:box-border ${className}`}
    >
      {currentCategoryItems.length > 0 ? (
        currentCategoryItems.map((item, index) => {
          const isActive = showItemHover && isItemActive(index);

          return (
            <div
              key={item.itemId}
              className={`w-[28.75rem] flex flex-col items-start transition-colors duration-200 ${
                isActive ? 'bg-[#ff0000]' : 'bg-transparent'
              } ${showItemHover ? 'cursor-pointer' : ''}`}
              onMouseEnter={() => showItemHover && handleItemHover(index)}
              style={isActive ? { backgroundColor: '#ff0000' } : undefined}
            >
              <div className="self-stretch flex items-center py-[0.625rem] px-[0.625rem] gap-[0.875rem]">
                <h2 className="m-0 relative text-[length:inherit] font-medium font-[inherit] inline-block max-w-[18.75rem]">
                  {item.nameRu}
                </h2>
                <div className="w-[1.563rem] relative bg-[#d9d9d9] h-[2.188rem]" />
                <div className="flex-1 flex items-center">
                  <h2 className="m-0 w-[7.688rem] relative text-[length:inherit] font-medium font-[inherit] flex items-center shrink-0">
                    {item.priceGrossDisplay}
                  </h2>
                </div>
              </div>
            </div>
          );
        })
      ) : (
        // Show placeholder when no items available for current category
        <div className="w-[28.75rem] flex flex-col items-center justify-center py-[2rem] text-[#a7a7a7]">
          <h2 className="m-0 text-[length:inherit] font-medium font-[inherit]">
            No items available in this category
          </h2>
        </div>
      )}
    </div>
  );
};

export default ItemList;
