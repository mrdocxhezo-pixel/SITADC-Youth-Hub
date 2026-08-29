/**
 * SITADC Youth Hub - Reusable Cascading Geographic Dropdown Component.
 *
 * Drives all Country -> Province -> District -> Constituency -> Ward selects
 * across the application from the centralized locations JSON API. This keeps
 * every geographic dropdown database-driven and never hard-coded in templates.
 *
 * The component auto-initializes every element with the `geo-` classes used by
 * the `locations/partials/geographic_dropdowns.html` include, but it also works
 * with any markup that carries the documented data attributes, so it can be
 * reused for forms, filters, modals, reports and dashboards.
 *
 * Markup contract (provided by the partial):
 *   <select class="geo-province" data-endpoint="..." data-parent-field="country"
 *           data-target="district">...</select>
 *
 * Behaviour:
 *   * loads children of the selected parent via ?parent_id / ?<level>_id
 *   * shows a loading state ("Loading ...")
 *   * shows an empty state ("No ... available")
 *   * clears dependent (downstream) fields when the parent changes
 *   * preserves preselected values on edit forms
 *   * handles API errors gracefully
 */
(function () {
  "use strict";

  var GEO_LEVELS = ["country", "province", "district", "constituency", "ward"];

  function loadSelect(select, endpoint, parentValue, paramName, placeholder) {
    if (!select) {
      return;
    }
    if (!parentValue) {
      clearSelect(select, placeholder);
      return;
    }
    select.disabled = true;
    select.innerHTML =
      '<option value="">' + (selectLoadingLabel(select) || "Loading...") + "</option>";

    var url =
      endpoint +
      (endpoint.indexOf("?") >= 0 ? "&" : "?") +
      encodeURIComponent(paramName) +
      "=" +
      encodeURIComponent(parentValue);

    fetch(url, {
      headers: { "Accept": "application/json" },
      credentials: "same-origin",
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Request failed with status " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        if (!Array.isArray(data)) {
          throw new Error("Unexpected response");
        }
        select.innerHTML = "";
        var option = document.createElement("option");
        option.value = "";
        option.textContent = placeholder;
        select.appendChild(option);

        if (data.length === 0) {
          option.textContent = selectEmptyLabel(select) || "No options available";
        } else {
          data.forEach(function (item) {
            var opt = document.createElement("option");
            opt.value = item.id;
            opt.textContent = item.name;
            select.appendChild(opt);
          });
        }
        select.disabled = false;
        triggerChange(select);
      })
      .catch(function (err) {
        select.disabled = false;
        select.innerHTML = "";
        var option = document.createElement("option");
        option.value = "";
        option.textContent = selectErrorLabel(select) || "Failed to load. Try again.";
        select.appendChild(option);
        console.error("Geographic dropdown error:", err);
      });
  }

  function selectLoadingLabel(select) {
    return select.getAttribute("data-loading-label");
  }
  function selectEmptyLabel(select) {
    return select.getAttribute("data-empty-label");
  }
  function selectErrorLabel(select) {
    return select.getAttribute("data-error-label");
  }

  function clearSelect(select, placeholder) {
    if (!select) {
      return;
    }
    select.innerHTML = "";
    var option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder || "Select";
    select.appendChild(option);
    select.disabled = false;
  }

  function triggerChange(select) {
    if (typeof window.CustomEvent === "function") {
      try {
        select.dispatchEvent(new CustomEvent("change"));
      } catch (e) {
        // older browsers
      }
    }
    select.dispatchEvent(new Event("change"));
  }

  function getParentSelect(select) {
    var parentFieldId = select.getAttribute("data-parent-field");
    if (!parentFieldId) {
      return null;
    }
    return document.getElementById(parentFieldId);
  }

  function ParamNameFor(level) {
    // country/province/district/constituency/ward
    return level + "_id";
  }

  function bind(select) {
    if (select._geoBound) {
      return;
    }
    select._geoBound = true;

    var level = select.getAttribute("data-geo-level");
    if (!level) {
      return;
    }
    var endpoint = select.getAttribute("data-endpoint");
    if (!endpoint) {
      return;
    }
    var targetId = select.getAttribute("data-target");
    var placeholder = select.options.length ? select.options[0].textContent : "Select";

    var refresh = function () {
      var parent = getParentSelect(select);
      var parentValue = parent ? parent.value : "";
      // On first load of an edit form, preserve the preselected value.
      var keep = parentValue && select.dataset.preserve;
      loadSelect(select, endpoint, parentValue, ParamNameFor(level), placeholder);

      // If editing and we already have a preselected value, restore it after load.
      if (keep && select.dataset.preserve) {
        var desired = select.dataset.preserve;
        var restore = function () {
          var found = Array.prototype.some.call(select.options, function (opt) {
            return opt.value === desired;
          });
          if (found) {
            select.value = desired;
            delete select.dataset.preserve;
          }
        };
        if (select._restoreTimer) {
          clearTimeout(select._restoreTimer);
        }
        select._restoreTimer = setTimeout(restore, 400);
      }
    };

    // When the parent changes, clear this field and its children, then reload.
    var parent = getParentSelect(select);
    if (parent) {
      parent.addEventListener("change", function () {
        clearSelect(select, placeholder);
        select.dataset.preserve = "";
        // Clear all downstream targets immediately.
        var target = document.getElementById(targetId);
        while (target) {
          clearSelect(target, target.options.length ? target.options[0].textContent : "Select");
          target = document.getElementById(target.getAttribute("data-target"));
        }
        refresh();
      });
    }

    // Initial load of a non-optional cascading select.
    if (!parent) {
      refresh();
    }
  }

  function init(root) {
    var scope = root || document;
    GEO_LEVELS.forEach(function (level) {
      var selects = scope.querySelectorAll('[data-geo-level="' + level + '"]');
      Array.prototype.forEach.call(selects, bind);
    });
  }

  // Auto-initialize on DOM ready.
  function onReady() {
    init(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }

  // Expose for dynamic forms / modals.
  window.SITADCLocations = {
    init: init,
    loadSelect: loadSelect,
  };
})();
