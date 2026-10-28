(function () {
    function getParts(target) {
        const groups = document.querySelectorAll(
            ".dash-dropdown-actions"
        );

        for (const group of groups) {
            const panel = group.parentElement;

            if (panel.contains(target)) {
                return {
                     buttons: Array.from(group.querySelectorAll(
                        "button.dash-dropdown-action-button"
                    )),
                    search: panel.querySelector("input")
                };
            }
        }

        return null;
    }

    window.addEventListener("keydown", function (event) {
        const parts = getParts(event.target);
        if (!parts || parts.buttons.length !== 2) return;

        const [selectAll, deselectAll] = parts.buttons;
        let next = null;

        const panel = parts.buttons[0].parentElement.parentElement;
        const firstOption = panel.querySelector(".dash-dropdown-option");
        const currentOption = event.target.closest(".dash-dropdown-option");

        if (
            event.key === "ArrowUp"
            && firstOption
            && currentOption === firstOption
        ) {
            next = deselectAll;
        }

        if (event.key === "ArrowDown" && event.target === parts.search) {
            next = selectAll;
        }


        if (event.key === "ArrowUp" && event.target === selectAll) {
            next = parts.search;
        }

        if (event.key === "ArrowDown" && event.target === selectAll) {
            next = deselectAll;
        }

        if (event.key === "ArrowUp" && event.target === deselectAll) {
            next = selectAll;
        }

        if (event.key === "Tab") {
            if (!event.shiftKey && event.target === parts.search) {
                next = selectAll;
            } else if (!event.shiftKey && event.target === selectAll) {
                next = deselectAll;
            } else if (event.shiftKey && event.target === deselectAll) {
                next = selectAll;
            } else if (event.shiftKey && event.target === selectAll) {
                next = parts.search;
            }
        }

        if (next) {
            event.preventDefault();
            event.stopImmediatePropagation();
            next.focus();
            next.scrollIntoView({
                block: "center",
                inline: "nearest"
            });
        }

        if (
            parts.buttons.includes(event.target)
            && (event.key === "Enter" || event.key === " ")
        ) {
            event.preventDefault();
            event.stopImmediatePropagation();
            event.target.click();
        }
    }, true);

    document.addEventListener("focusin", function (event) {
        if (event.target.matches(".dash-dropdown-action-button")) {
            event.target.style.outline = "2px solid #0B1F5E";
        }
    });

    document.addEventListener("focusout", function (event) {
        if (event.target.matches(".dash-dropdown-action-button")) {
            event.target.style.outline = "";
        }
    });
})();
