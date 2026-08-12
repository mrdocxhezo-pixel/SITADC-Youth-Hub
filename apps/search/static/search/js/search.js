/* Enterprise Search module behaviour
 * Keeps the entity-type refinements and the save-search hidden fields in
 * sync so the sidebar "Save search" action can reconstruct the query.
 */

(function () {
    "use strict";

    function typesQueryString() {
        var checked = document.querySelectorAll('input[name="types"]:checked');
        var values = [];
        Array.prototype.forEach.call(checked, function (input) {
            values.push(input.value);
        });
        return values.join(",");
    }

    function syncHiddenTypes() {
        var hidden = document.querySelector('input#id_types[type="hidden"]');
        if (hidden) {
            hidden.value = typesQueryString();
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var queryInput = document.querySelector('input[name="q"]');
        var hiddenQuery = document.querySelector('input#id_query[type="hidden"]');
        var typesFieldset = document.querySelector('fieldset');

        syncHiddenTypes();

        if (typesFieldset) {
            typesFieldset.addEventListener("change", syncHiddenTypes);
        }

        if (queryInput && hiddenQuery) {
            hiddenQuery.value = queryInput.value.trim();
            queryInput.addEventListener("input", function () {
                hiddenQuery.value = queryInput.value.trim();
            });
        }

        var saveForm = document.querySelector('form[action*="saved_create"]');
        if (saveForm && queryInput && hiddenQuery) {
            saveForm.addEventListener("submit", function () {
                hiddenQuery.value = queryInput.value.trim();
                syncHiddenTypes();
            });
        }
    });
})();