// OrderProcessingStatusesHandle.tsx
// Shows order processing statuses in simple column layout
// Displays order status, FSM state progression, and processing steps
// Countdown starts only after all statuses are complete

import { FunctionComponent, useEffect, useState, useRef } from "react";
import { useOrder } from "../contexts/OrderContext";
import { OrderStatus, FSMState } from "../models/domain/order";
import MediaDisplay from "./MediaDisplay";

export interface OrderProcessingStatusesHandleProps {
  className?: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

const OrderProcessingStatusesHandle: FunctionComponent<OrderProcessingStatusesHandleProps> = ({
  className = "",
  onComplete,
  onError
}) => {
  const { currentOrder } = useOrder();
  const [countdown, setCountdown] = useState<number | null>(null); // null = not started yet
  const [countdownPaused, setCountdownPaused] = useState<boolean>(false);

  // Track order status progression
  const [orderStatusHistory, setOrderStatusHistory] = useState<OrderStatus[]>([OrderStatus.PENDING]);
  const lastSeenOrderStatus = useRef<OrderStatus | null>(null);

  // Track FSM state progression
  const [fsmStateHistory, setFsmStateHistory] = useState<FSMState[]>([FSMState.INIT]);
  const lastSeenFsmState = useRef<FSMState | null>(null);

  // Display statuses for processing steps (what user sees)
  const [fiscalizationStatus, setFiscalizationStatus] = useState<string>('...');
  const [paymentStatus, setPaymentStatus] = useState<string>('...');
  const [printingStatus, setPrintingStatus] = useState<string>('...');
  const [transmissionStatus, setTransmissionStatus] = useState<string>('...');

  // Info messages to show while waiting for status
  const [showFiscalizationInfo, setShowFiscalizationInfo] = useState(true); // Start showing immediately
  const [showPaymentInfo, setShowPaymentInfo] = useState(false);
  const [showPrintingInfo, setShowPrintingInfo] = useState(false);
  const [showTransmissionInfo, setShowTransmissionInfo] = useState(false);

  // Track if we've already processed failures
  const hasProcessedFailure = useRef(false);

  // Track order status changes
  useEffect(() => {
    if (!currentOrder) return;

    const currentStatus = currentOrder.status;
    if (currentStatus !== lastSeenOrderStatus.current) {
      lastSeenOrderStatus.current = currentStatus;
      setOrderStatusHistory(prev => {
        // Only add if not already in history
        if (!prev.includes(currentStatus)) {
          return [...prev, currentStatus];
        }
        return prev;
      });
    }
  }, [currentOrder]);

  // Track FSM state changes
  useEffect(() => {
    if (!currentOrder) return;

    const currentFsmState = currentOrder.fsm_state;
    if (currentFsmState !== lastSeenFsmState.current) {
      lastSeenFsmState.current = currentFsmState;
      setFsmStateHistory(prev => {
        // Only add if not already in history
        if (!prev.includes(currentFsmState)) {
          return [...prev, currentFsmState];
        }
        return prev;
      });
    }
  }, [currentOrder]);

  // Listen to FSM events and update processing statuses immediately
  useEffect(() => {
    if (!currentOrder) return;

    const events = currentOrder.fsm_event_history || [];

    // Check for fiscalization
    const hasFiscalizationSucceeded = events.some(e => e.event === 'FISCALIZATION_SUCCEEDED');
    const hasFiscalizationFailed = events.some(e => e.event === 'FISCALIZATION_FAILED');

    if (fiscalizationStatus === '...') {
      if (hasFiscalizationFailed) {
        setFiscalizationStatus('ОШИБКА');
        setShowFiscalizationInfo(false); // Hide blinking info
        // Mark remaining as ОТМЕНА
        if (!hasProcessedFailure.current) {
          hasProcessedFailure.current = true;
          setPaymentStatus('ОТМЕНА');
          setPrintingStatus('ОТМЕНА');
          setTransmissionStatus('ОТМЕНА');
        }
      } else if (hasFiscalizationSucceeded) {
        setFiscalizationStatus('ВЫПОЛНЕНО');
        setShowFiscalizationInfo(false); // Hide blinking info
        setShowPaymentInfo(true); // Show next blinking info
      }
    }

    // Check for payment (only if not cancelled)
    if (paymentStatus === '...' && !hasProcessedFailure.current) {
      const hasPaymentSucceeded = events.some(e => e.event === 'PAYMENT_SUCCEEDED');
      const hasPaymentFailed = events.some(e => e.event === 'PAYMENT_FAILED' || e.event === 'INACTIVITY_TIMEOUT' || e.event === 'USER_CANCELED');

      if (hasPaymentFailed) {
        setPaymentStatus('ОШИБКА');
        setShowPaymentInfo(false); // Hide blinking info
        // Mark remaining as ОТМЕНА
        if (!hasProcessedFailure.current) {
          hasProcessedFailure.current = true;
          setPrintingStatus('ОТМЕНА');
          setTransmissionStatus('ОТМЕНА');
        }
      } else if (hasPaymentSucceeded) {
        setPaymentStatus('ВЫПОЛНЕНО');
        setShowPaymentInfo(false); // Hide blinking info
        setShowPrintingInfo(true); // Show next blinking info
      }
    }

    // Check for printing (only if not cancelled)
    if (printingStatus === '...' && !hasProcessedFailure.current) {
      const hasPrintingSucceeded = events.some(e => e.event === 'PRINTING_SUCCEEDED');
      const hasPrintingFailed = events.some(e => e.event === 'PRINTING_FAILED_OR_TIMEOUT');

      if (hasPrintingFailed) {
        setPrintingStatus('ОШИБКА');
        setShowPrintingInfo(false); // Hide blinking info
      } else if (hasPrintingSucceeded) {
        setPrintingStatus('ВЫПОЛНЕНО');
        setShowPrintingInfo(false); // Hide blinking info
        setShowTransmissionInfo(true); // Show next blinking info
      }
    }

    // Check for transmission (only if not cancelled)
    if (transmissionStatus === '...' && !hasProcessedFailure.current) {
      const hasKDSConfirmation = events.some(e => e.event === 'KDS_CONFIRMATION');
      const hasKDSError = events.some(e => e.event === 'KDS_ERROR_OR_NO_RESPONSE');

      if (hasKDSError) {
        setTransmissionStatus('ОШИБКА');
        setShowTransmissionInfo(false); // Hide blinking info
      } else if (hasKDSConfirmation) {
        setTransmissionStatus('ВЫПОЛНЕНО');
        setShowTransmissionInfo(false); // Hide blinking info
      }
    }
  }, [currentOrder, fiscalizationStatus, paymentStatus, printingStatus, transmissionStatus]);

  // Start countdown when order reaches terminal status (COMPLETED, FAILED, or CANCELLED)
  // FSM events are just informational - order status is the main trigger
  useEffect(() => {
    const isTerminalState =
      currentOrder?.status === OrderStatus.COMPLETED ||
      currentOrder?.status === OrderStatus.FAILED ||
      currentOrder?.status === OrderStatus.CANCELLED;

    if (isTerminalState && countdown === null) {
      console.log('✅ Order terminal state reached:', currentOrder?.status, '- starting countdown');
      setCountdown(10);
    }
  }, [currentOrder?.status, countdown]);

  // Countdown timer (only runs when countdown is not null and not paused)
  useEffect(() => {
    if (countdown === null || countdown === 0 || countdownPaused) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev === null) return null;
        if (prev <= 1) {
          clearInterval(timer);
          // Defer callback to avoid setState during render
          setTimeout(() => {
            if (currentOrder?.status === OrderStatus.COMPLETED) {
              onComplete?.();
            } else if (currentOrder?.status === OrderStatus.FAILED || currentOrder?.status === OrderStatus.CANCELLED) {
              onError?.('Order failed');
            } else {
              onComplete?.(); // Default to complete
            }
          }, 0);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, countdownPaused, currentOrder?.status, onComplete, onError]);

  if (!currentOrder) {
    return null;
  }

  return (
    <div className={`fixed inset-0 flex flex-col z-50 ${className}`} style={{ backgroundColor: '#1e1e1e' }}>
      {/* Background media layer (video or image) */}
      <MediaDisplay
        cacheKey="orderhandling_order_handling"
        alt="Order handling background"
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        loading="eager"
      />

      {/* Dark overlay for text readability */}
      <div className="absolute inset-0 bg-black/50 pointer-events-none" />

      <div className="font-mono text-[#c0c0c0] w-full max-w-[1920px] mx-auto px-16 pt-16 relative z-10">

        {/* Top Row: Order Number (left) and Pickup/PIN (right corner) */}
        <div className="flex justify-between items-start mb-16">
          {/* Order Number - Left */}
          <div className="text-4xl font-bold">
            ORDER №{currentOrder.order_id}
          </div>

          {/* Pickup and PIN - Right corner, only if order completed */}
          {currentOrder.status === OrderStatus.COMPLETED && currentOrder.pickup_number && (
            <div className="flex flex-col items-end text-5xl font-bold space-y-4">
              <div>PICKUP: {currentOrder.pickup_number}</div>
              {currentOrder.pin_code && <div>PIN CODE: {currentOrder.pin_code}</div>}
            </div>
          )}
        </div>

        {/* Left Column Layout */}
        <div className="flex flex-col items-start space-y-12">

          {/* Processing Steps - Bigger Font, Top Left */}
          <div>
            <div className="text-3xl mb-6 text-[#ffff00]">[ PROCESSING STEPS ]</div>
            <div className="space-y-5 text-3xl">
              <div>
                FISCALISATION: <span style={{ color: fiscalizationStatus === 'ВЫПОЛНЕНО' ? '#00ff00' : fiscalizationStatus === 'ОШИБКА' ? '#ff0000' : fiscalizationStatus === 'ОТМЕНА' ? '#808080' : '#ffff00' }}>{fiscalizationStatus}</span>
                {showFiscalizationInfo && (
                  <span className="text-3xl text-[#00ff00] animate-pulse ml-4">
                    ИДЕТ ПРОЦЕСС ФИСКАЛИЗАЦИИ. НЕ ЗАБУДЬТЕ СВОЙ ЧЕК
                  </span>
                )}
              </div>
              <div>
                PAYMENT: <span style={{ color: paymentStatus === 'ВЫПОЛНЕНО' ? '#00ff00' : paymentStatus === 'ОШИБКА' ? '#ff0000' : paymentStatus === 'ОТМЕНА' ? '#808080' : '#ffff00' }}>{paymentStatus}</span>
                {showPaymentInfo && (
                  <span className="text-3xl text-[#00ff00] animate-pulse ml-4">
                    СЛЕДУЙТЕ ИНСТРУКЦИЯМ НА ПЛАТЕЖНОМ ТЕРМИНАЛЕ
                  </span>
                )}
              </div>
              <div>
                PRINTING: <span style={{ color: printingStatus === 'ВЫПОЛНЕНО' ? '#00ff00' : printingStatus === 'ОШИБКА' ? '#ff0000' : printingStatus === 'ОТМЕНА' ? '#808080' : '#ffff00' }}>{printingStatus}</span>
                {showPrintingInfo && (
                  <span className="text-3xl text-[#00ff00] animate-pulse ml-4">
                    ИДЕТ ПРОЦЕСС ПЕЧАТИ
                  </span>
                )}
              </div>
              <div>
                TRANSMISSION TO KDS: <span style={{ color: transmissionStatus === 'ВЫПОЛНЕНО' ? '#00ff00' : transmissionStatus === 'ОШИБКА' ? '#ff0000' : transmissionStatus === 'ОТМЕНА' ? '#808080' : '#ffff00' }}>{transmissionStatus}</span>
                {showTransmissionInfo && (
                  <span className="text-3xl text-[#00ff00] animate-pulse ml-4">
                    ИДЕТ ПЕРЕДАЧА НА АВТОМАТИЗИРОВАННУЮ КУХНЮ
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Horizontal ASCII Divider - 1/6 screen width (320px) */}
          <div className="text-2xl" style={{ width: '320px' }}>
            {'═'.repeat(40)}
          </div>

          {/* Order Status and FSM State - Same Column Below Divider */}
          <div className="space-y-12">
            {/* Order Status */}
            <div>
              <div className="text-2xl mb-6 text-[#ffff00]">[ ORDER STATUS ]</div>
              <div className="space-y-3 text-xl">
                {orderStatusHistory.map((status, index) => (
                  <div key={index} style={{ color: status === 'COMPLETED' ? '#00ff00' : status === 'FAILED' ? '#ff0000' : status === 'CANCELLED' ? '#808080' : '#c0c0c0' }}>
                    {status}
                  </div>
                ))}
              </div>
            </div>

            {/* FSM State */}
            <div>
              <div className="text-2xl mb-6 text-[#ffff00]">[ FSM STATE ]</div>
              <div className="space-y-3 text-xl">
                {fsmStateHistory.map((state, index) => (
                  <div key={index}>{state}</div>
                ))}
              </div>
            </div>
          </div>

        </div>

        {/* Countdown - Large semi-transparent overlay */}
        {countdown !== null && (
          <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-10">
            <div className="text-[20rem] font-bold text-[#00ff00]" style={{ opacity: 0.3 }}>
              {countdown}
            </div>
          </div>
        )}

        {/* Debug Mode - Pause/Resume Countdown */}
        {countdown !== null && (
          <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-20">
            <button
              onClick={() => setCountdownPaused(!countdownPaused)}
              className="px-8 py-4 text-2xl font-bold bg-[#ff0000] text-[#ffff00] border-4 border-[#ffff00] cursor-pointer hover:bg-[#cc0000]"
            >
              !DEBUG MODE! press to {countdownPaused ? 'CONTINUE' : 'STOP'} countdown !DEBUG MODE!
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default OrderProcessingStatusesHandle;
