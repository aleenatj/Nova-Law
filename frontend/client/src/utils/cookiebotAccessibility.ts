/**
 * Utility functions to fix Cookiebot accessibility issues.
 * Fixes aria-labelledby and aria-describedby attributes that reference
 * elements without proper text content or aria-label attributes.
 * Also ensures forms have proper submit buttons for accessibility.
 */

// Performance optimization: Cache for accessible text checks to avoid repeated DOM queries
const accessibleTextCache = new WeakMap<Element, boolean>();
const MAX_RECURSION_DEPTH = 5; // Prevent infinite recursion

// Check if we're in development mode
const isDev = import.meta.env?.DEV ?? import.meta.env?.MODE === "development";

/**
 * Conditionally logs messages only in development mode.
 */
function devLog(...args: unknown[]): void {
    if (isDev) {
        console.log(...args);
    }
}

function devWarn(...args: unknown[]): void {
    if (isDev) {
        console.warn(...args);
    }
}

/**
 * Checks if an element has accessible text content.
 * An element is considered accessible if it has:
 * - Text content (trimmed)
 * - An aria-label attribute with content
 * - An aria-labelledby that references an accessible element (recursive check)
 * 
 * Uses caching to avoid repeated checks on the same element.
 */
function hasAccessibleText(element: Element | null, depth = 0): boolean {
    if (!element) {
        return false;
    }

    // Prevent infinite recursion
    if (depth > MAX_RECURSION_DEPTH) {
        return false;
    }

    // Check cache first
    if (accessibleTextCache.has(element)) {
        return accessibleTextCache.get(element)!;
    }

    let result = false;

    // Check for aria-label
    const ariaLabel = element.getAttribute("aria-label");
    if (ariaLabel && ariaLabel.trim().length > 0) {
        result = true;
    } else {
        // Check for text content
        const textContent = element.textContent?.trim() || "";
        if (textContent.length > 0) {
            result = true;
        } else {
            // Check for aria-labelledby (recursive, with depth limit)
            const ariaLabelledBy = element.getAttribute("aria-labelledby");
            if (ariaLabelledBy) {
                const referencedIds = ariaLabelledBy.split(/\s+/);
                for (const id of referencedIds) {
                    const referencedElement = document.getElementById(id);
                    if (referencedElement && hasAccessibleText(referencedElement, depth + 1)) {
                        result = true;
                        break;
                    }
                }
            }
        }
    }

    // Cache the result
    accessibleTextCache.set(element, result);
    return result;
}

/**
 * Fixes aria-labelledby and aria-describedby attributes on an element.
 * If the referenced element doesn't have accessible text, the attribute is removed
 * or a fallback aria-label is added to the referenced element.
 */
function fixAriaAttributes(element: Element): void {
    // Fix aria-labelledby
    const ariaLabelledBy = element.getAttribute("aria-labelledby");
    if (ariaLabelledBy) {
        const referencedIds = ariaLabelledBy.split(/\s+/);
        let validIds: string[] = [];

        for (const id of referencedIds) {
            const referencedElement = document.getElementById(id);
            if (referencedElement) {
                if (hasAccessibleText(referencedElement)) {
                    validIds.push(id);
                } else {
                    // Try to add an aria-label based on common patterns
                    // Check if it's a tab/button that might have text nearby
                    const textContent = referencedElement.textContent?.trim() || "";
                    if (textContent.length > 0) {
                        referencedElement.setAttribute("aria-label", textContent);
                        validIds.push(id);
                    } else {
                        // If we can't fix it, remove from the list
                        devWarn(
                            `Cookiebot accessibility: aria-labelledby references element #${id} without accessible text. Removing reference.`,
                        );
                    }
                }
            } else {
                devWarn(
                    `Cookiebot accessibility: aria-labelledby references non-existent element #${id}. Removing reference.`,
                );
            }
        }

        // Update or remove the attribute
        if (validIds.length > 0) {
            element.setAttribute("aria-labelledby", validIds.join(" "));
        } else {
            element.removeAttribute("aria-labelledby");
        }
    }

    // Fix aria-describedby
    const ariaDescribedBy = element.getAttribute("aria-describedby");
    if (ariaDescribedBy) {
        const referencedIds = ariaDescribedBy.split(/\s+/);
        let validIds: string[] = [];

        for (const id of referencedIds) {
            const referencedElement = document.getElementById(id);
            if (referencedElement) {
                if (hasAccessibleText(referencedElement)) {
                    validIds.push(id);
                } else {
                    // Try to add an aria-label based on common patterns
                    const textContent = referencedElement.textContent?.trim() || "";
                    if (textContent.length > 0) {
                        referencedElement.setAttribute("aria-label", textContent);
                        validIds.push(id);
                    } else {
                        devWarn(
                            `Cookiebot accessibility: aria-describedby references element #${id} without accessible text. Removing reference.`,
                        );
                    }
                }
            } else {
                devWarn(
                    `Cookiebot accessibility: aria-describedby references non-existent element #${id}. Removing reference.`,
                );
            }
        }

        // Update or remove the attribute
        if (validIds.length > 0) {
            element.setAttribute("aria-describedby", validIds.join(" "));
        } else {
            element.removeAttribute("aria-describedby");
        }
    }
}

/**
 * Checks if a form has a submit button.
 * A form is considered to have a submit button if it contains:
 * - An input element with type="submit"
 * - A button element with type="submit" or no type attribute (defaults to submit)
 * - An element with role="button" that can submit the form
 */
function formHasSubmitButton(form: HTMLFormElement): boolean {
    // Check for input[type="submit"]
    const submitInput = form.querySelector('input[type="submit"]');
    if (submitInput) {
        return true;
    }

    // Check for button[type="submit"] or button without type (defaults to submit)
    const submitButton = form.querySelector('button[type="submit"], button:not([type])');
    if (submitButton) {
        return true;
    }

    // Check for elements with role="button" that might act as submit buttons
    const buttonRole = form.querySelector('[role="button"]');
    if (buttonRole) {
        // Check if it's within the form context
        return form.contains(buttonRole);
    }

    return false;
}

/**
 * Checks if a form can be submitted via Enter key.
 * This is typically true if the form has at least one input field.
 */
function formSupportsEnterKeySubmission(form: HTMLFormElement): boolean {
    const hasInputFields =
        form.querySelectorAll('input:not([type="hidden"]), textarea, select').length > 0;
    return hasInputFields;
}

/**
 * Adds a hidden submit button to a form for accessibility compliance.
 * The button is hidden visually but accessible to screen readers.
 */
function addHiddenSubmitButton(form: HTMLFormElement): void {
    // Check if we've already added a hidden submit button
    const existingHiddenSubmit = form.querySelector(
        'input[type="submit"][data-cookiebot-accessibility-fix]',
    );
    if (existingHiddenSubmit) {
        return;
    }

    const hiddenSubmit = document.createElement('input');
    hiddenSubmit.type = 'submit';
    hiddenSubmit.setAttribute('data-cookiebot-accessibility-fix', 'true');
    hiddenSubmit.style.cssText =
        'position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border-width: 0;';
    hiddenSubmit.setAttribute('aria-hidden', 'true');
    hiddenSubmit.setAttribute('tabindex', '-1');

    // Add the hidden submit button to the form
    form.appendChild(hiddenSubmit);
}

/**
 * Checks if an element is within a Cookiebot container or is a Cookiebot element.
 */
function isCookiebotElement(element: Element): boolean {
    const id = element.id || "";
    const className = element.className?.toString() || "";

    return (
        id.includes("Cookiebot") ||
        id.includes("CybotCookiebot") ||
        className.includes("Cookiebot") ||
        className.includes("CybotCookiebot")
    );
}

/**
 * Checks if a form is a Cookiebot form (either has Cookiebot classes/IDs or is within a Cookiebot container).
 */
function isCookiebotForm(form: HTMLFormElement): boolean {
    // Check if the form itself is a Cookiebot element
    if (isCookiebotElement(form)) {
        return true;
    }

    // Check if form is within a Cookiebot container by traversing up the DOM tree
    let parent = form.parentElement;
    while (parent) {
        if (isCookiebotElement(parent)) {
            return true;
        }
        parent = parent.parentElement;
    }

    return false;
}

/**
 * Fixes forms without submit buttons by adding a hidden submit button.
 * This ensures accessibility compliance while not interfering with Cookiebot's UI.
 */
function fixCookiebotForms(): void {
    // Find all forms in the document
    const allForms = document.querySelectorAll("form");

    // Filter to only Cookiebot forms
    const cookiebotForms = Array.from(allForms).filter((form) =>
        isCookiebotForm(form as HTMLFormElement),
    );

    // Use a Set to deduplicate
    const allCookiebotForms = new Set(cookiebotForms as HTMLFormElement[]);

    // Check each form for submit buttons
    allCookiebotForms.forEach((form) => {
        if (!formHasSubmitButton(form)) {
            // Add a hidden submit button for accessibility compliance.
            // The button can be hidden since forms typically support submission via Enter key.
            // This satisfies accessibility requirements without interfering with Cookiebot's UI.
            addHiddenSubmitButton(form);
            devLog(
                'Cookiebot accessibility: Added hidden submit button to form without submit button.',
            );
        }
    });
}

/**
 * Scans the document for all Cookiebot elements and fixes their accessibility attributes.
 */
function fixCookiebotAccessibility(): void {
    // Find all elements with Cookiebot classes or IDs
    const cookiebotElements = document.querySelectorAll(
        '[id*="Cookiebot"], [id*="CybotCookiebot"], [class*="Cookiebot"], [class*="CybotCookiebot"]',
    );

    cookiebotElements.forEach((element) => {
        // Fix attributes on the element itself
        fixAriaAttributes(element);

        // Also check if this element has aria-labelledby or aria-describedby
        if (
            element.hasAttribute("aria-labelledby") ||
            element.hasAttribute("aria-describedby")
        ) {
            fixAriaAttributes(element);
        }
    });

    // Also check all elements with aria-labelledby or aria-describedby in the document
    // that reference Cookiebot elements
    const allElementsWithAria = document.querySelectorAll(
        '[aria-labelledby], [aria-describedby]',
    );

    allElementsWithAria.forEach((element) => {
        // Only process if it's within or references Cookiebot elements
        const ariaLabelledBy = element.getAttribute("aria-labelledby");
        const ariaDescribedBy = element.getAttribute("aria-describedby");
        const allReferences = [
            ...(ariaLabelledBy?.split(/\s+/) || []),
            ...(ariaDescribedBy?.split(/\s+/) || []),
        ];

        const isCookiebotRelated =
            element.id?.includes("Cookiebot") ||
            element.id?.includes("CybotCookiebot") ||
            element.className?.toString().includes("Cookiebot") ||
            element.className?.toString().includes("CybotCookiebot") ||
            allReferences.some(
                (id) =>
                    document.getElementById(id)?.id?.includes("Cookiebot") ||
                    document.getElementById(id)?.id?.includes("CybotCookiebot"),
            );

        if (isCookiebotRelated) {
            fixAriaAttributes(element);
        }
    });

    // Fix forms without submit buttons
    fixCookiebotForms();
}

// Performance optimization: Debounce and throttle for MutationObserver
let fixTimeout: number | null = null;
let isFixing = false;
let observerInstance: MutationObserver | null = null;

/**
 * Initializes a MutationObserver to watch for Cookiebot DOM changes
 * and automatically fix accessibility issues when they appear.
 * Uses debouncing and requestIdleCallback for performance.
 */
function watchCookiebotChanges(): void {
    // Prevent multiple observers
    if (observerInstance) {
        return;
    }

    // Initial fix - use requestIdleCallback if available for non-blocking execution
    if (typeof requestIdleCallback !== "undefined") {
        requestIdleCallback(() => {
            fixCookiebotAccessibility();
        });
    } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
            fixCookiebotAccessibility();
        }, 0);
    }

    // Set up MutationObserver to watch for Cookiebot changes
    observerInstance = new MutationObserver((mutations) => {
        let shouldFix = false;

        // Quick check to see if any mutations are Cookiebot-related
        for (const mutation of mutations) {
            // Check if any added nodes are Cookiebot-related
            const addedNodes = Array.from(mutation.addedNodes);
            for (const node of addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const element = node as Element;
                    // Fast string checks first
                    const id = element.id || "";
                    const className = element.className?.toString() || "";
                    if (
                        id.includes("Cookiebot") ||
                        id.includes("CybotCookiebot") ||
                        className.includes("Cookiebot") ||
                        className.includes("CybotCookiebot")
                    ) {
                        shouldFix = true;
                        break;
                    }
                    // Only do expensive querySelector if quick checks pass
                    if (element.querySelector('[id*="Cookiebot"], [id*="CybotCookiebot"]')) {
                        shouldFix = true;
                        break;
                    }
                    // Check if a form was added
                    if (element.tagName === "FORM" || element.querySelector("form")) {
                        shouldFix = true;
                        break;
                    }
                }
            }

            if (shouldFix) break;

            // Check if attributes changed on Cookiebot elements
            if (mutation.type === "attributes" && mutation.target instanceof Element) {
                const element = mutation.target;
                const id = element.id || "";
                const className = element.className?.toString() || "";
                if (
                    (mutation.attributeName === "aria-labelledby" ||
                        mutation.attributeName === "aria-describedby") &&
                    (id.includes("Cookiebot") ||
                        id.includes("CybotCookiebot") ||
                        className.includes("Cookiebot") ||
                        className.includes("CybotCookiebot"))
                ) {
                    shouldFix = true;
                    break;
                }
            }
        }

        if (shouldFix && !isFixing) {
            // Clear existing timeout
            if (fixTimeout !== null) {
                clearTimeout(fixTimeout);
            }

            // Debounce the fix to avoid excessive calls
            fixTimeout = window.setTimeout(() => {
                isFixing = true;
                // Use requestIdleCallback for non-blocking execution
                if (typeof requestIdleCallback !== "undefined") {
                    requestIdleCallback(
                        () => {
                            fixCookiebotAccessibility();
                            isFixing = false;
                        },
                        { timeout: 1000 }, // Max 1 second wait
                    );
                } else {
                    // Fallback: use setTimeout with small delay
                    setTimeout(() => {
                        fixCookiebotAccessibility();
                        isFixing = false;
                    }, 150);
                }
                fixTimeout = null;
            }, 100);
        }
    });

    // Start observing the document body for changes
    observerInstance.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["aria-labelledby", "aria-describedby", "type"],
    });
}

// Track initialization to prevent multiple calls
let isInitialized = false;

/**
 * Initializes Cookiebot accessibility fixes.
 * Should be called after the DOM is ready and Cookiebot script is loaded.
 * Prevents duplicate initialization for performance.
 */
export function initializeCookiebotAccessibility(): void {
    // Prevent duplicate initialization
    if (isInitialized) {
        return;
    }
    isInitialized = true;

    // Wait for DOM to be ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            watchCookiebotChanges();
        });
    } else {
        watchCookiebotChanges();
    }

    // Also watch for Cookiebot script load (but don't call watchCookiebotChanges again if already called)
    if (typeof window !== "undefined" && (window as any).Cookiebot) {
        // Cookiebot already loaded, observer already set up above
        return;
    }

    // Poll for Cookiebot to load (with timeout)
    // Only set up observer if not already done
    const maxAttempts = 50; // 5 seconds max
    let attempts = 0;
    const checkCookiebot = setInterval(() => {
        attempts++;
        if ((window as any).Cookiebot || attempts >= maxAttempts) {
            clearInterval(checkCookiebot);
            // Observer should already be set up, just trigger initial fix
            if (observerInstance && typeof requestIdleCallback !== "undefined") {
                requestIdleCallback(() => {
                    fixCookiebotAccessibility();
                });
            }
        }
    }, 100);
}


