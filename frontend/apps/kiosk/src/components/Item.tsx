import { FunctionComponent, useMemo, type CSSProperties } from "react";

export type ItemType = {
  className?: string;
  itemName?: string;

  /** Variant props */
  property1?: string;

  /** Style props */
  itemNameMargin?: CSSProperties["margin"];
  itemPictureBackgroundColor?: CSSProperties["backgroundColor"];
  itemPictureMargin?: CSSProperties["margin"];
};

const Item: FunctionComponent<ItemType> = ({
  className = "",
  itemName,
  itemNameMargin,
  itemPictureBackgroundColor,
  itemPictureMargin,
}) => {
  const itemNameStyle: CSSProperties = useMemo(() => {
    return {
      margin: itemNameMargin,
    };
  }, [itemNameMargin]);

  const itemPictureStyle: CSSProperties = useMemo(() => {
    return {
      backgroundColor: itemPictureBackgroundColor,
      margin: itemPictureMargin,
    };
  }, [itemPictureBackgroundColor, itemPictureMargin]);

  return (
    <div
      className={`flex flex-col items-start text-left text-[1.625rem] text-[#fff] font-['PT_Sans'] ${className}`}
    >
      <div className="w-[28.75rem] flex items-center py-[0.625rem] px-[0rem] box-border gap-[0.875rem]">
        <h2
          className="m-0 relative text-[length:inherit] font-medium font-[inherit] inline-block max-w-[18.75rem]"
          style={itemNameStyle}
        >
          {itemName}
        </h2>
        <div
          className="w-[1.563rem] relative bg-[#d9d9d9] h-[2.188rem]"
          style={itemPictureStyle}
        />
        <div className="flex-1 flex items-center">
          <h2 className="m-0 w-[7.688rem] relative text-[length:inherit] font-medium font-[inherit] flex items-center shrink-0">
            380₽
          </h2>
        </div>
      </div>
      <div className="w-[28.813rem] relative border-[#a7a7a7] border-dashed border-t-[1px] box-border h-[0.063rem]" />
    </div>
  );
};

export default Item;
