import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2, ChevronLeft, ChevronRight, Image as ImageIcon } from 'lucide-react';

export default function CanvasPreview({
  templateUrl,
  fields,
  onUpdateField,
  selectedFieldKey,
  onSelectField,
  csvRows,
  currentRowIndex,
  onRowChange,
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [zoom, setZoom] = useState(0.4);
  const [naturalSize, setNaturalSize] = useState({ width: 2000, height: 1414 });
  const [isDragging, setIsDragging] = useState(false);
  const [activeDragField, setActiveDragField] = useState(null);
  const dragStartPos = useRef({ x: 0, y: 0, initialFieldX: 0, initialFieldY: 0 });

  const currentSampleRow = csvRows && csvRows.length > 0 ? csvRows[currentRowIndex] : null;

  useEffect(() => {
    if (!templateUrl) return;
    const img = new Image();
    img.src = templateUrl;
    img.onload = () => {
      setNaturalSize({ width: img.naturalWidth || 2000, height: img.naturalHeight || 1414 });
    };
  }, [templateUrl]);

  // Fit canvas scale automatically based on workspace size
  const handleFitToScreen = () => {
    if (!containerRef.current || !templateUrl) return;
    const containerWidth = containerRef.current.clientWidth - 80;
    const scale = Math.min(containerWidth / naturalSize.width, 0.45);
    setZoom(scale > 0 ? scale : 0.4);
  };

  useEffect(() => {
    if (templateUrl) {
      handleFitToScreen();
    }
  }, [naturalSize.width, templateUrl]);

  const handleMouseDown = (e, fieldKey) => {
    e.stopPropagation();
    onSelectField(fieldKey);
    const field = fields.find((f) => f.field === fieldKey);
    if (!field) return;

    setIsDragging(true);
    setActiveDragField(fieldKey);
    dragStartPos.current = {
      x: e.clientX,
      y: e.clientY,
      initialFieldX: field.x,
      initialFieldY: field.y,
    };
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !activeDragField) return;
    const deltaX = (e.clientX - dragStartPos.current.x) / zoom;
    const deltaY = (e.clientY - dragStartPos.current.y) / zoom;

    const newX = Math.round(dragStartPos.current.initialFieldX + deltaX);
    const newY = Math.round(dragStartPos.current.initialFieldY + deltaY);

    onUpdateField(activeDragField, { x: newX, y: newY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setActiveDragField(null);
  };

  return (
    <div
      className="workspace"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {!templateUrl ? (
        /* Empty Canvas Placeholder matching user screenshot */
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#6b7280', gap: '16px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '12px', border: '2px dashed #223354', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ImageIcon size={32} style={{ color: '#4b5563' }} />
          </div>
          <span style={{ fontSize: '0.95rem', fontWeight: 500, color: '#9ca3af' }}>
            Upload a template to preview
          </span>
        </div>
      ) : (
        /* Canvas container scaled with zoom */
        <div
          className="canvas-wrapper checkerboard"
          ref={canvasRef}
          style={{
            width: `${naturalSize.width * zoom}px`,
            height: `${naturalSize.height * zoom}px`,
            position: 'relative',
          }}
        >
          {/* Background certificate template image */}
          <img
            src={templateUrl}
            alt="Certificate Template"
            style={{
              width: '100%',
              height: '100%',
              display: 'block',
              pointerEvents: 'none',
            }}
          />

          {/* Text Field Overlays */}
          {fields.map((fieldSpec) => {
            if (!fieldSpec.enabled) return null;

            const isSelected = selectedFieldKey === fieldSpec.field;
            const displayValue = currentSampleRow
              ? (currentSampleRow[fieldSpec.field] || `{${fieldSpec.field}}`)
              : `{${fieldSpec.field}}`;

            // Scaled styles based on zoom
            const scaledX = fieldSpec.x * zoom;
            const scaledY = fieldSpec.y * zoom;
            const scaledFontSize = Math.max(12, fieldSpec.size * zoom);

            let textAlignTransform = 'translate(0, 0)';
            if (fieldSpec.align === 'center') {
              textAlignTransform = 'translate(-50%, 0)';
            } else if (fieldSpec.align === 'right') {
              textAlignTransform = 'translate(-100%, 0)';
            }

            return (
              <div
                key={fieldSpec.field}
                className={`overlay-field ${isSelected ? 'selected' : ''}`}
                onMouseDown={(e) => handleMouseDown(e, fieldSpec.field)}
                style={{
                  left: `${scaledX}px`,
                  top: `${scaledY}px`,
                  transform: textAlignTransform,
                  fontSize: `${scaledFontSize}px`,
                  fontFamily: fieldSpec.font_path.replace('.ttf', ''),
                  fontWeight: fieldSpec.bold ? 'bold' : 'normal',
                  color: fieldSpec.color || '#000000',
                  zIndex: isSelected ? 30 : 20,
                }}
              >
                {displayValue}

                {isSelected && (
                  <>
                    <div className="handle" style={{ top: '-4px', left: '-4px' }} />
                    <div className="handle" style={{ top: '-4px', right: '-4px' }} />
                    <div className="handle" style={{ bottom: '-4px', left: '-4px' }} />
                    <div className="handle" style={{ bottom: '-4px', right: '-4px' }} />
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Floating Bottom Toolbar */}
      {templateUrl && (
        <div className="canvas-toolbar">
          <button
            className="toolbar-btn"
            title="Zoom Out"
            onClick={() => setZoom((z) => Math.max(0.15, z - 0.05))}
          >
            <ZoomOut size={16} />
          </button>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            {Math.round(zoom * 100)}%
          </span>
          <button
            className="toolbar-btn"
            title="Zoom In"
            onClick={() => setZoom((z) => Math.min(1.5, z + 0.05))}
          >
            <ZoomIn size={16} />
          </button>
          <button className="toolbar-btn" title="Fit to Screen" onClick={handleFitToScreen}>
            <Maximize2 size={16} />
          </button>

          {csvRows && csvRows.length > 0 && (
            <>
              <div className="toolbar-divider" />
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <button
                  className="toolbar-btn"
                  title="Previous CSV Row"
                  onClick={() => onRowChange(Math.max(0, currentRowIndex - 1))}
                  disabled={currentRowIndex === 0}
                >
                  <ChevronLeft size={16} />
                </button>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Row {currentRowIndex + 1} of {csvRows.length}
                </span>
                <button
                  className="toolbar-btn"
                  title="Next CSV Row"
                  onClick={() => onRowChange(Math.min(csvRows.length - 1, currentRowIndex + 1))}
                  disabled={currentRowIndex >= csvRows.length - 1}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
