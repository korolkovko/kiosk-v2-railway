import { FunctionComponent } from "react";

export type DividersVerticalType = {
  className?: string;
};

const DividersVertical: FunctionComponent<DividersVerticalType> = ({
  className = "",
}) => {
  return (
    <div
      className={`h-[67.5rem] bg-[#000] flex items-center gap-[0.125rem] mq1725:w-full mq1725:h-[0.375rem] ${className}`}
    >
      <div className="self-stretch w-[0.125rem] relative bg-[#d9d9d9]" />
      <div className="self-stretch w-[0.125rem] relative bg-[#d9d9d9]" />
    </div>
  );
};

export default DividersVertical;
