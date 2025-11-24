(function () {
    'use strict';


    function setupCoordinateSelectionOnImage(mapSVG) {
        const pt = mapSVG.createSVGPoint();
        let isDragging = false;
        let startX, startY;
        let selectionRect = null;

        // Helper function to convert screen coordinates to SVG coordinates
        function screenToSVG(clientX, clientY) {
            pt.x = clientX;
            pt.y = clientY;
            return pt.matrixTransform(mapSVG.getScreenCTM().inverse());
        }

        // Helper function to calculate rectangle dimensions
        function calculateRectDimensions(currentX, currentY) {
            return {
                x: Math.min(startX, currentX),
                y: Math.min(startY, currentY),
                width: Math.abs(currentX - startX),
                height: Math.abs(currentY - startY)
            };
        }

        // Helper function to update form fields
        function updateFormFields(x, y, width, height) {
            function setField(field, value) {
                field.value = value;
                // Trigger change events for any listeners
                field.dispatchEvent(new Event('change', {bubbles: true}));
            }

            const xField = document.querySelector('#id_x');
            const yField = document.querySelector('#id_y');
            if (xField && yField) {
                setField(xField, Math.round(x));
                setField(yField, Math.round(y));

                const widthField = document.querySelector('#id_width');
                const heightField = document.querySelector('#id_height');
                if (width && height && widthField && heightField) {
                    setField(widthField, Math.round(width));
                    setField(heightField, Math.round(height));
                }
            }
        }


        // Mouse down - start selection
        function mouseDown(event) {
            event.preventDefault();
            isDragging = true;

            const svgCoords = screenToSVG(event.clientX, event.clientY);
            startX = svgCoords.x;
            startY = svgCoords.y;

            // Create selection rectangle
            selectionRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');

            selectionRect.setAttribute('x', startX);
            selectionRect.setAttribute('y', startY);
            selectionRect.setAttribute('width', '0');
            selectionRect.setAttribute('height', '0');
            selectionRect.setAttribute('fill', 'rgba(0, 123, 255, 0.2)');
            selectionRect.setAttribute('stroke', '#007bff');
            selectionRect.style.pointerEvents = 'none';

            mapSVG.appendChild(selectionRect);
        }

        // Mouse move - update selection
        function mouseMove(event) {
            if (!isDragging || !selectionRect) {
                return;
            }

            event.preventDefault();
            const svgCoords = screenToSVG(event.clientX, event.clientY);
            const rect = calculateRectDimensions(svgCoords.x, svgCoords.y);

            selectionRect.setAttribute('x', rect.x);
            selectionRect.setAttribute('y', rect.y);
            selectionRect.setAttribute('width', rect.width);
            selectionRect.setAttribute('height', rect.height);
        }

        // Helper function to clean up selection rectangle
        function cleanupSelectionRect() {
            if (selectionRect?.parentNode) {
                selectionRect.parentNode.removeChild(selectionRect);
            }
            selectionRect = null;
            isDragging = false;
        }

        // Mouse up - complete selection
        function mouseUp(event) {
            if (!isDragging || !selectionRect) {
                return;
            }

            event.preventDefault();

            const svgCoords = screenToSVG(event.clientX, event.clientY);
            const rect = calculateRectDimensions(svgCoords.x, svgCoords.y);

            // Update point or rect field depending on click or drag
            if (rect.width > 5 && rect.height > 5) {
                updateFormFields(rect.x, rect.y, rect.width, rect.height);
                console.log(`Selection: X=${Math.round(rect.x)}, Y=${Math.round(rect.y)}, ` +
                    `Width=${Math.round(rect.width)}, Height=${Math.round(rect.height)}`);
            } else {
                updateFormFields(rect.x, rect.y);
                console.log(`Click: X=${Math.round(rect.x)}, Y=${Math.round(rect.y)}`);
            }

            // Remove selection rectangle after a short delay
            setTimeout(() => {
                cleanupSelectionRect();
            }, 500);
        }


        // Handle mouse leave to clean up if user drags outside
        function mouseLeave(){
            if (isDragging && selectionRect) {
                cleanupSelectionRect();
            }
        }

        const image = mapSVG.querySelector('image');
        image.addEventListener('mousedown', mouseDown);
        image.addEventListener('mousemove', mouseMove);
        image.addEventListener('mouseup', mouseUp);

        mapSVG.addEventListener('mouseleave', mouseLeave);
    }

    function setupCoordinateSelection() {
        document.querySelectorAll('.map-svg').forEach(mapSVG => {
            setupCoordinateSelectionOnImage(mapSVG);
        });
    }

    function setupHoverListener(listener) {
        document.addEventListener('map.hover', event => {
            const pk = event.detail.pk;
            const type = event.detail.type;
            if (pk !== undefined) {
                let selector = `[data-${type}="${pk}"]`;
                let element = listener.querySelector(selector);
                if (element) {
                    element.classList.add('hover');
                    element.classList.add('table-active');
                }
            } else {
                listener.querySelectorAll('[data-desk], [data-room]').forEach(desk => {
                    desk.classList.remove('hover');
                    desk.classList.remove('table-active');
                });
            }
        });
    }

    function setupHoverDispatcher(source) {
        function dispatchHoverEvent(source, pk, type) {
            source.dispatchEvent(new CustomEvent('map.hover', {
                bubbles: true, detail: {pk, type}
            }));
        }

        function registerListener(listener, pk, type) {
            listener.addEventListener('mouseenter', () => {
                dispatchHoverEvent(listener, pk, type);
            });
            listener.addEventListener('mouseleave', () => {
                dispatchHoverEvent(listener);
            });
        }

        source.querySelectorAll('[data-desk]').forEach(desk => {
            registerListener(desk, desk.getAttribute('data-desk'), 'desk');
        });

        source.querySelectorAll('[data-room]').forEach(room => {
            registerListener(room, room.getAttribute('data-room'), 'room');
        });
    }

    function setupMapHover() {
        document.querySelectorAll('.map-svg').forEach(map => {
            setupHoverListener(map);
            setupHoverDispatcher(map);
        });
    }

    function setupTableHover() {
        document.querySelectorAll('.table').forEach(table => {
            setupHoverListener(table);
            setupHoverDispatcher(table);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        setupMapHover();
        setupTableHover();
        setupCoordinateSelection();

        document.addEventListener('iommi.loading.end', () => {
            setupMapHover();
            setupTableHover();
            setupCoordinateSelection();
        });
    });

    console.log('js loaded');
})();
