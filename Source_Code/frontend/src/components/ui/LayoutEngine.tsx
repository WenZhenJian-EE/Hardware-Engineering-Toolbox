import React, { useState, useEffect, useRef } from 'react';
import { GripVertical } from 'lucide-react';

// Configuration interface for layout initialization
export interface LayoutConfig {
  panelKey: string;
  activeTab?: string; // Tab index or 'default' if no tabs
  defaultCards: string[];
  defaultColumns: Record<string, 'left' | 'right'>;
  defaultSpans: Record<string, number>;
  defaultHeights: Record<string, number>;
}

export function useDragDeckLayout({
  panelKey,
  activeTab = 'default',
  defaultCards,
  defaultColumns,
  defaultSpans,
  defaultHeights
}: LayoutConfig) {
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const handleResize = () => setIsDesktop(window.innerWidth >= 1024);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Helper to validate if saved cards overlap perfectly with defaultCards
  const isValidOrder = (order: any) => {
    if (!order || !Array.isArray(order) || order.length !== defaultCards.length) return false;
    return defaultCards.every(c => order.includes(c));
  };

  // 1. Cards Order State
  const [cardsOrder, setCardsOrder] = useState<Record<string, string[]>>(() => {
    const saved = localStorage.getItem(`hb_${panelKey}_cards_order`);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object' && isValidOrder(parsed[activeTab])) return parsed;
      } catch (e) {}
    }
    return { [activeTab]: defaultCards };
  });

  // 2. Card Spans State (1-12 horizontal grid columns)
  const [cardSpans, setCardSpans] = useState<Record<string, Record<string, number>>>(() => {
    const saved = localStorage.getItem(`hb_${panelKey}_card_spans`);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          const activeSpans = parsed[activeTab];
          if (activeSpans && Object.keys(activeSpans).some(k => defaultCards.includes(k))) return parsed;
        }
      } catch (e) {}
    }
    return { [activeTab]: defaultSpans };
  });

  // 3. Card Heights State (vertical height in pixels)
  const [cardHeights, setCardHeights] = useState<Record<string, Record<string, number>>>(() => {
    const saved = localStorage.getItem(`hb_${panelKey}_card_heights`);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          const activeHeights = parsed[activeTab];
          if (activeHeights && Object.keys(activeHeights).some(k => defaultCards.includes(k))) return parsed;
        }
      } catch (e) {}
    }
    return { [activeTab]: defaultHeights };
  });

  // 4. Card Column Assignment State ('left' | 'right')
  const [cardColumns, setCardColumns] = useState<Record<string, Record<string, 'left' | 'right'>>>(() => {
    const saved = localStorage.getItem(`hb_${panelKey}_card_columns`);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          const activeCols = parsed[activeTab];
          if (activeCols && Object.keys(activeCols).some(k => defaultCards.includes(k))) return parsed;
        }
      } catch (e) {}
    }
    return { [activeTab]: defaultColumns };
  });

  const [draggedKey, setDraggedKey] = useState<string | null>(null);

  // Sync state if activeTab changes and does not exist in the record yet
  useEffect(() => {
    const readFromStorage = <T,>(suffix: string, fallback: T): T => {
      const saved = localStorage.getItem(`hb_${panelKey}_${suffix}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (parsed && typeof parsed === 'object') {
            return parsed;
          }
        } catch (e) {}
      }
      return fallback;
    };

    const savedOrder = readFromStorage<Record<string, string[]>>('cards_order', {});
    const savedSpans = readFromStorage<Record<string, Record<string, number>>>('card_spans', {});
    const savedHeights = readFromStorage<Record<string, Record<string, number>>>('card_heights', {});
    const savedCols = readFromStorage<Record<string, Record<string, 'left' | 'right'>>>('card_columns', {});

    const orderForTab = savedOrder[activeTab];
    const isOrderValid = isValidOrder(orderForTab);

    const finalOrder = isOrderValid ? savedOrder : { ...savedOrder, [activeTab]: defaultCards };
    const finalSpans = savedSpans[activeTab] ? savedSpans : { ...savedSpans, [activeTab]: defaultSpans };
    const finalHeights = savedHeights[activeTab] ? savedHeights : { ...savedHeights, [activeTab]: defaultHeights };
    const finalCols = savedCols[activeTab] ? savedCols : { ...savedCols, [activeTab]: defaultColumns };

    setCardsOrder(prev => JSON.stringify(prev) === JSON.stringify(finalOrder) ? prev : finalOrder);
    setCardSpans(prev => JSON.stringify(prev) === JSON.stringify(finalSpans) ? prev : finalSpans);
    setCardHeights(prev => JSON.stringify(prev) === JSON.stringify(finalHeights) ? prev : finalHeights);
    setCardColumns(prev => JSON.stringify(prev) === JSON.stringify(finalCols) ? prev : finalCols);

    if (!isOrderValid) {
      localStorage.setItem(`hb_${panelKey}_cards_order`, JSON.stringify(finalOrder));
    }
    if (!savedSpans[activeTab]) {
      localStorage.setItem(`hb_${panelKey}_card_spans`, JSON.stringify(finalSpans));
    }
    if (!savedHeights[activeTab]) {
      localStorage.setItem(`hb_${panelKey}_card_heights`, JSON.stringify(finalHeights));
    }
    if (!savedCols[activeTab]) {
      localStorage.setItem(`hb_${panelKey}_card_columns`, JSON.stringify(finalCols));
    }
  }, [panelKey, activeTab, defaultCards, defaultColumns, defaultSpans, defaultHeights]);

  // DRAG & DROP HANDLERS
  const handleDragStart = (e: React.DragEvent, key: string) => {
    setDraggedKey(key);
    e.dataTransfer.setData('text/plain', key);
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
    }
  };

  const handleDragEnd = () => {
    setDraggedKey(null);
  };

  const handleDragEnter = (e: React.DragEvent, targetKey: string) => {
    if (!draggedKey || draggedKey === targetKey) return;

    const targetCol = cardColumns[activeTab]?.[targetKey] ?? 'right';
    const draggedCol = cardColumns[activeTab]?.[draggedKey] ?? 'right';

    // If dragged card enters a different column, auto-assign it to the target column
    if (draggedCol !== targetCol) {
      const updatedCols = {
        ...cardColumns,
        [activeTab]: {
          ...cardColumns[activeTab],
          [draggedKey]: targetCol
        }
      };
      setCardColumns(updatedCols);
      localStorage.setItem(`hb_${panelKey}_card_columns`, JSON.stringify(updatedCols));
    }

    const currentOrder = cardsOrder[activeTab] || defaultCards;
    const newOrder = [...currentOrder];
    const dragIdx = newOrder.indexOf(draggedKey);
    const targetIdx = newOrder.indexOf(targetKey);
    if (dragIdx !== -1 && targetIdx !== -1) {
      newOrder.splice(dragIdx, 1);
      newOrder.splice(targetIdx, 0, draggedKey);
      const updated = { ...cardsOrder, [activeTab]: newOrder };
      setCardsOrder(updated);
      localStorage.setItem(`hb_${panelKey}_cards_order`, JSON.stringify(updated));
    }
  };

  const handleDropOnColumn = (e: React.DragEvent, col: 'left' | 'right') => {
    if (!draggedKey) return;
    setCardColumns(prev => {
      const updated = {
        ...prev,
        [activeTab]: {
          ...prev[activeTab],
          [draggedKey]: col
        }
      };
      localStorage.setItem(`hb_${panelKey}_card_columns`, JSON.stringify(updated));
      return updated;
    });
  };

  // WIDTH & HEIGHT RESIZE HANDLERS
  const handleResizeStart = (e: React.MouseEvent, key: string) => {
    e.preventDefault();
    const startX = e.clientX;
    const startSpan = cardSpans[activeTab]?.[key] ?? 8;

    // Dynamically calculate grid column width from active DOM grid
    const gridEl = document.querySelector('.grid-cols-12');
    const gridWidth = gridEl ? gridEl.clientWidth : (window.innerWidth - 256);
    const colWidth = gridWidth / 12;

    let rafId: number | null = null;
    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const diffX = moveEvent.clientX - startX;
        const spanDiff = Math.round(diffX / colWidth);
        const newSpan = Math.max(2, Math.min(12, startSpan + spanDiff));

        setCardSpans(prev => {
          const tabSpans = prev[activeTab] ? { ...prev[activeTab] } : {};
          tabSpans[key] = newSpan;

          const currentCols = cardColumns[activeTab] || defaultColumns;
          const resizedCol = currentCols[key] ?? 'right';
          const remaining = 12 - newSpan;

          // Auto synchronize opposite column width split for all other cards
          Object.keys(currentCols).forEach(k => {
            const colOfCard = currentCols[k] ?? 'right';
            if (colOfCard !== resizedCol) {
              tabSpans[k] = remaining;
            }
          });

          const updated = {
            ...prev,
            [activeTab]: tabSpans
          };
          localStorage.setItem(`hb_${panelKey}_card_spans`, JSON.stringify(updated));
          return updated;
        });
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleHeightResizeStart = (e: React.MouseEvent, key: string) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = cardHeights[activeTab]?.[key] ?? 300;

    let rafId: number | null = null;
    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const diffY = moveEvent.clientY - startY;
        // Snapping to discrete steps of 50px for standardized sizing
        const heightDiff = Math.round(diffY / 50) * 50;
        const newHeight = Math.max(150, Math.min(1500, startHeight + heightDiff));

        setCardHeights(prev => {
          const updated = {
            ...prev,
            [activeTab]: {
              ...prev[activeTab],
              [key]: newHeight
            }
          };
          localStorage.setItem(`hb_${panelKey}_card_heights`, JSON.stringify(updated));
          return updated;
        });
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleHeightResizeStartTop = (e: React.MouseEvent, key: string) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = cardHeights[activeTab]?.[key] ?? 300;

    let rafId: number | null = null;
    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const diffY = moveEvent.clientY - startY;
        // Resizing from top: moving mouse down decreases height, moving mouse up increases height
        const heightDiff = Math.round(diffY / 50) * 50;
        const newHeight = Math.max(150, Math.min(1500, startHeight - heightDiff));

        setCardHeights(prev => {
          const updated = {
            ...prev,
            [activeTab]: {
              ...prev[activeTab],
              [key]: newHeight
            }
          };
          localStorage.setItem(`hb_${panelKey}_card_heights`, JSON.stringify(updated));
          return updated;
        });
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleResetCardHeight = (key: string) => {
    setCardHeights(prev => {
      const tabHeights = prev[activeTab] ? { ...prev[activeTab] } : {};
      tabHeights[key] = defaultHeights[key] ?? 300;
      const updated = {
        ...prev,
        [activeTab]: tabHeights
      };
      localStorage.setItem(`hb_${panelKey}_card_heights`, JSON.stringify(updated));
      return updated;
    });
  };

  const handleResetLayout = () => {
    const defaultColsRecord = { [activeTab]: defaultColumns };
    const defaultSpansRecord = { [activeTab]: defaultSpans };
    const defaultHeightsRecord = { [activeTab]: defaultHeights };
    const defaultOrdersRecord = { [activeTab]: defaultCards };

    setCardColumns(defaultColsRecord);
    setCardSpans(defaultSpansRecord);
    setCardHeights(defaultHeightsRecord);
    setCardsOrder(defaultOrdersRecord);

    localStorage.removeItem(`hb_${panelKey}_card_columns`);
    localStorage.removeItem(`hb_${panelKey}_card_spans`);
    localStorage.removeItem(`hb_${panelKey}_card_heights`);
    localStorage.removeItem(`hb_${panelKey}_cards_order`);
  };

  // Filter left vs right column elements
  const activeOrder = cardsOrder[activeTab] || defaultCards;
  const leftCards = activeOrder.filter(k => (cardColumns[activeTab]?.[k] ?? defaultColumns[k] ?? 'right') === 'left');
  const rightCards = activeOrder.filter(k => (cardColumns[activeTab]?.[k] ?? defaultColumns[k] ?? 'right') === 'right');

  // Compute active spans by dynamically querying the first left column card
  const leftCardInCol = activeOrder.find(k => (cardColumns[activeTab]?.[k] ?? defaultColumns[k] ?? 'right') === 'left');
  const leftSpanRaw = leftCardInCol ? (cardSpans[activeTab]?.[leftCardInCol] ?? defaultSpans[leftCardInCol] ?? 4) : 4;
  const leftSpan = rightCards.length === 0 ? 12 : leftSpanRaw;
  const rightSpan = 12 - leftSpan;

  return {
    isDesktop,
    draggedKey,
    leftCards,
    rightCards,
    leftSpan,
    rightSpan,
    cardHeights: cardHeights[activeTab] || defaultHeights,
    handleDragStart,
    handleDragEnter,
    handleDragEnd,
    handleDropOnColumn,
    handleResizeStart,
    handleHeightResizeStart,
    handleHeightResizeStartTop,
    handleResetCardHeight,
    handleResetLayout
  };
}

// ------------------------------------------------------------------
// standardized wrapper components
// ------------------------------------------------------------------

interface DragDeckProps {
  isDesktop: boolean;
  draggedKey: string | null;
  leftSpan: number;
  rightSpan: number;
  leftCards: string[];
  rightCards: string[];
  renderCard: (key: string) => React.ReactNode;
  onDropOnColumn: (e: React.DragEvent, col: 'left' | 'right') => void;
  onDragStart?: any;
  onDragEnter?: any;
  onDragEnd?: any;
}

export const DragDeck: React.FC<DragDeckProps> = ({
  isDesktop,
  draggedKey,
  leftSpan,
  rightSpan,
  leftCards,
  rightCards,
  renderCard,
  onDropOnColumn,
  onDragStart,
  onDragEnter,
  onDragEnd
}) => {
  return (
    <div className="w-full max-w-full grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
      {/* Left Column */}
      <div
        style={{ gridColumn: isDesktop ? `span ${leftSpan}` : undefined }}
        className="flex flex-col gap-6"
      >
        {leftCards.map(key => (
          <React.Fragment key={key}>
            {renderCard(key)}
          </React.Fragment>
        ))}
        {draggedKey && isDesktop && (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => onDropOnColumn(e, 'left')}
            style={{ height: '80px' }}
            className="border-2 border-dashed border-teal-500/50 bg-teal-950/10 rounded-xl flex items-center justify-center text-xs text-teal-400 font-medium hover:bg-teal-950/20 hover:border-teal-500 transition-all cursor-pointer"
          >
            Drop here to dock at bottom of left column
          </div>
        )}
      </div>

      {/* Right Column */}
      <div
        style={{ gridColumn: isDesktop ? `span ${rightSpan}` : undefined }}
        className="flex flex-col gap-6"
      >
        {rightCards.map(key => (
          <React.Fragment key={key}>
            {renderCard(key)}
          </React.Fragment>
        ))}
        {draggedKey && isDesktop && (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => onDropOnColumn(e, 'right')}
            style={{ height: '80px' }}
            className="border-2 border-dashed border-teal-500/50 bg-teal-950/10 rounded-xl flex items-center justify-center text-xs text-teal-400 font-medium hover:bg-teal-950/20 hover:border-teal-500 transition-all cursor-pointer"
          >
            Drop here to dock at bottom of right column
          </div>
        )}
      </div>
    </div>
  );
};

interface DragCardProps {
  cardKey: string;
  height: number;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnter: (e: React.DragEvent) => void;
  onDragEnd: () => void;
  onResizeStart: (e: React.MouseEvent, key: string) => void;
  onHeightResizeStart: (e: React.MouseEvent, key: string) => void;
  onHeightResizeStartTop?: (e: React.MouseEvent, key: string) => void;
  onResetHeight?: () => void;
  onResetLayout?: any;
  children: React.ReactNode;
}

export const DragCard: React.FC<DragCardProps> = ({
  cardKey,
  height,
  onDragStart,
  onDragEnter,
  onDragEnd,
  onResizeStart,
  onHeightResizeStart,
  onHeightResizeStartTop,
  onResetHeight,
  onResetLayout,
  children
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cardEl = cardRef.current;
    if (!cardEl) return;

    // Find the scrollable inner container (the one with overflow-y-auto)
    const scrollableEl = cardEl.querySelector('.overflow-y-auto') as HTMLDivElement | null;
    if (!scrollableEl) return;

    const handleWheel = (e: WheelEvent) => {
      const { scrollTop, scrollHeight, clientHeight } = scrollableEl;
      const isScrollable = scrollHeight > clientHeight;

      if (!isScrollable) {
        // Let browser handle native page scroll
        return;
      }

      const isAtTop = e.deltaY < 0 && scrollTop <= 1;
      const isAtBottom = e.deltaY > 0 && scrollTop + clientHeight >= scrollHeight - 1.5;
      
      if (!isAtTop && !isAtBottom) {
        // Only intercept and scroll inside the card when we are NOT at boundary
        e.preventDefault();
        scrollableEl.scrollTop += e.deltaY;
      }
    };

    // Use passive: false to allow preventing default behavior
    cardEl.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      cardEl.removeEventListener('wheel', handleWheel);
    };
  }, [height, children]); // Re-attach if height or children content updates

  return (
    <div
      ref={cardRef}
      draggable
      onDragStart={onDragStart}
      onDragEnter={onDragEnter}
      onDragEnd={onDragEnd}
      style={{ height: height ? `${height}px` : 'auto' }}
      className="relative group cursor-grab active:cursor-grabbing transition-[box-shadow,border-color] duration-150 w-full mb-6"
    >
      {/* Grab handle icon on hover */}
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-30 p-1 hover:bg-slate-800 rounded">
        <GripVertical className="w-3.5 h-3.5 text-slate-400 hover:text-slate-200" />
      </div>

      {/* Resize handle (Horizontal Right) */}
      <div
        onMouseDown={(e) => onResizeStart(e, cardKey)}
        className="absolute top-0 -right-1 w-2 h-full cursor-col-resize hover:bg-cyan-500/30 active:bg-cyan-500 z-35 transition-colors border-r border-cyan-500/10 hover:border-cyan-400/50"
        title="Double-click to reset size / Drag to resize column width"
      />

      {/* Resize handle (Vertical Top) */}
      {onHeightResizeStartTop && (
        <div
          onMouseDown={(e) => onHeightResizeStartTop(e, cardKey)}
          onDoubleClick={onResetHeight}
          className="absolute -top-1 left-0 w-full h-2 cursor-row-resize hover:bg-cyan-500/30 active:bg-cyan-500 z-35 transition-colors border-t border-cyan-500/10 hover:border-cyan-400/50"
          title="Double-click to reset height / Drag to resize height"
        />
      )}

      {/* Resize handle (Vertical Bottom) */}
      <div
        onMouseDown={(e) => onHeightResizeStart(e, cardKey)}
        onDoubleClick={onResetHeight}
        className="absolute -bottom-1 left-0 w-full h-2 cursor-row-resize hover:bg-cyan-500/30 active:bg-cyan-500 z-35 transition-colors border-b border-cyan-500/10 hover:border-cyan-400/50"
        title="Double-click to reset height / Drag to resize height"
      />

      {/* Content slot */}
      {children}
    </div>
  );
};
