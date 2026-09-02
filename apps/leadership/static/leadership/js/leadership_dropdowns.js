/**
 * SITADC Youth Hub - Cascading Leadership & Organizational Dropdowns
 *
 * Drives cascading relationships for:
 *   1. Functional Hierarchy:
 *      Organizational Unit -> Directorate -> Department -> Program & Technical Management -> Team
 *   2. Geographical Hierarchy:
 *      Region -> District -> Community -> Team
 *
 * Features:
 *   - Preserves preselected values when editing an existing leadership profile.
 *   - Database-backed via authenticated JSON endpoints.
 *   - Displays loading states ("Loading...") and empty states ("No options available" / "No teams available").
 *   - Keyboard accessible and responsive.
 */

(function () {
  "use strict";

  const API_ENDPOINTS = {
    directorates: "/organizations/api/directorates/",
    departments: "/organizations/api/departments/",
    ptm: "/organizations/api/program-technical/",
    teams: "/organizations/api/teams/",
    positions: "/organizations/api/positions/",
    units: "/organizations/api/units/",
    districts: "/locations/api/districts/",
    constituencies: "/locations/api/constituencies/",
    wards: "/locations/api/wards/",
  };

  function fetchJson(url) {
    return fetch(url, {
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    }).then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      return res.json();
    });
  }

  function populateSelect(selectEl, items, placeholderText, selectedValue, emptyText) {
    if (!selectEl) return;

    selectEl.innerHTML = "";

    // Placeholder option
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = placeholderText;
    selectEl.appendChild(defaultOption);

    if (!items || items.length === 0) {
      defaultOption.textContent = emptyText || placeholderText;
      selectEl.disabled = false;
      return;
    }

    let hasSelected = false;
    items.forEach((item) => {
      const opt = document.createElement("option");
      opt.value = item.id;
      opt.textContent = item.name || item.title;
      if (selectedValue && String(item.id) === String(selectedValue)) {
        opt.selected = true;
        hasSelected = true;
      }
      selectEl.appendChild(opt);
    });

    selectEl.disabled = false;

    // Trigger change event if needed
    if (hasSelected) {
      selectEl.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function setLoading(selectEl, loadingText) {
    if (!selectEl) return;
    selectEl.disabled = true;
    selectEl.innerHTML = `<option value="">${loadingText || "Loading..."}</option>`;
  }

  document.addEventListener("DOMContentLoaded", function () {
    const directorateSelect = document.getElementById("id_directorate");
    const departmentSelect = document.getElementById("id_department");
    const ptmSelect = document.getElementById("id_program_technical_management");
    const regionSelect = document.getElementById("id_region");
    const districtSelect = document.getElementById("id_district");
    const communitySelect = document.getElementById("id_community");
    const teamSelect = document.getElementById("id_team");

    // Track initial values for edit forms
    const initialValues = {
      directorate: directorateSelect ? directorateSelect.value : "",
      department: departmentSelect ? departmentSelect.value : "",
      ptm: ptmSelect ? ptmSelect.value : "",
      region: regionSelect ? regionSelect.value : "",
      district: districtSelect ? districtSelect.value : "",
      community: communitySelect ? communitySelect.value : "",
      team: teamSelect ? teamSelect.value : "",
    };

    let isInitialLoad = true;

    // 1. Directorate Change -> Update Department and PTM options
    if (directorateSelect) {
      directorateSelect.addEventListener("change", function () {
        const directorateId = this.value;
        const targetDeptValue = isInitialLoad ? initialValues.department : "";
        const targetPtmValue = isInitialLoad ? initialValues.ptm : "";

        if (departmentSelect) {
          if (!directorateId) {
            // If no directorate, reload all active departments
            fetchJson(API_ENDPOINTS.departments)
              .then((depts) => {
                populateSelect(
                  departmentSelect,
                  depts,
                  "Select Department",
                  targetDeptValue,
                  "No departments available"
                );
              })
              .catch(() => {
                departmentSelect.disabled = false;
              });
          } else {
            setLoading(departmentSelect, "Loading departments...");
            fetchJson(`${API_ENDPOINTS.departments}?directorate_id=${encodeURIComponent(directorateId)}`)
              .then((depts) => {
                populateSelect(
                  departmentSelect,
                  depts,
                  "Select Department",
                  targetDeptValue,
                  "No departments available for this Directorate"
                );
              })
              .catch(() => {
                departmentSelect.disabled = false;
              });
          }
        }

        if (ptmSelect && !departmentSelect?.value) {
          if (directorateId) {
            setLoading(ptmSelect, "Loading technical roles...");
            fetchJson(`${API_ENDPOINTS.ptm}?directorate_id=${encodeURIComponent(directorateId)}`)
              .then((roles) => {
                populateSelect(
                  ptmSelect,
                  roles,
                  "Select Program / Technical Management",
                  targetPtmValue,
                  "No technical roles available for this Directorate"
                );
              })
              .catch(() => {
                ptmSelect.disabled = false;
              });
          }
        }
      });
    }

    // 2. Department Change -> Update PTM and Teams
    if (departmentSelect) {
      departmentSelect.addEventListener("change", function () {
        const departmentId = this.value;
        const targetPtmValue = isInitialLoad ? initialValues.ptm : "";

        if (ptmSelect) {
          if (!departmentId) {
            const directorateId = directorateSelect ? directorateSelect.value : "";
            const url = directorateId
              ? `${API_ENDPOINTS.ptm}?directorate_id=${encodeURIComponent(directorateId)}`
              : API_ENDPOINTS.ptm;

            fetchJson(url)
              .then((roles) => {
                populateSelect(
                  ptmSelect,
                  roles,
                  "Select Program / Technical Management",
                  targetPtmValue,
                  "No technical roles available"
                );
              })
              .catch(() => {
                ptmSelect.disabled = false;
              });
          } else {
            setLoading(ptmSelect, "Loading technical roles...");
            fetchJson(`${API_ENDPOINTS.ptm}?department_id=${encodeURIComponent(departmentId)}`)
              .then((roles) => {
                populateSelect(
                  ptmSelect,
                  roles,
                  "Select Program / Technical Management",
                  targetPtmValue,
                  "No technical roles available for this Department"
                );
              })
              .catch(() => {
                ptmSelect.disabled = false;
              });
          }
        }
      });
    }

    // 3. Region Change -> Update District
    if (regionSelect && districtSelect) {
      regionSelect.addEventListener("change", function () {
        const regionId = this.value;
        const targetDistrictValue = isInitialLoad ? initialValues.district : "";

        if (!regionId) {
          fetchJson(`${API_ENDPOINTS.units}?unit_type=DISTRICT`)
            .then((districts) => {
              populateSelect(
                districtSelect,
                districts,
                "Select District",
                targetDistrictValue,
                "No districts available"
              );
            })
            .catch(() => {
              districtSelect.disabled = false;
            });
        } else {
          setLoading(districtSelect, "Loading districts...");
          fetchJson(`${API_ENDPOINTS.units}?unit_type=DISTRICT&parent_id=${encodeURIComponent(regionId)}`)
            .then((districts) => {
              populateSelect(
                districtSelect,
                districts,
                "Select District",
                targetDistrictValue,
                "No districts available for this Region"
              );
            })
            .catch(() => {
              districtSelect.disabled = false;
            });
        }
      });
    }

    // 4. District Change -> Update Community
    if (districtSelect && communitySelect) {
      districtSelect.addEventListener("change", function () {
        const districtId = this.value;
        const targetCommValue = isInitialLoad ? initialValues.community : "";

        if (!districtId) {
          fetchJson(`${API_ENDPOINTS.units}?unit_type=COMMUNITY`)
            .then((comms) => {
              populateSelect(
                communitySelect,
                comms,
                "Select Community",
                targetCommValue,
                "No communities available"
              );
            })
            .catch(() => {
              communitySelect.disabled = false;
            });
        } else {
          setLoading(communitySelect, "Loading communities...");
          fetchJson(`${API_ENDPOINTS.units}?unit_type=COMMUNITY&parent_id=${encodeURIComponent(districtId)}`)
            .then((comms) => {
              populateSelect(
                communitySelect,
                comms,
                "Select Community",
                targetCommValue,
                "No communities available for this District"
              );
            })
            .catch(() => {
              communitySelect.disabled = false;
            });
        }
      });
    }

    // 5. Community Change -> Update Team
    if (communitySelect && teamSelect) {
      communitySelect.addEventListener("change", function () {
        const communityId = this.value;
        const targetTeamValue = isInitialLoad ? initialValues.team : "";

        if (!communityId) {
          fetchJson(`${API_ENDPOINTS.teams}`)
            .then((teams) => {
              populateSelect(
                teamSelect,
                teams,
                "Select Team",
                targetTeamValue,
                "No teams available"
              );
            })
            .catch(() => {
              teamSelect.disabled = false;
            });
        } else {
          setLoading(teamSelect, "Loading teams...");
          fetchJson(`${API_ENDPOINTS.teams}?parent_id=${encodeURIComponent(communityId)}`)
            .then((teams) => {
              populateSelect(
                teamSelect,
                teams,
                "Select Team",
                targetTeamValue,
                "No teams available"
              );
            })
            .catch(() => {
              teamSelect.disabled = false;
            });
        }
      });
    }

    // Initial trigger for edit form if directorate or region is preselected
    if (initialValues.directorate && directorateSelect) {
      directorateSelect.dispatchEvent(new Event("change"));
    }
    if (initialValues.region && regionSelect) {
      regionSelect.dispatchEvent(new Event("change"));
    }

    // End initial load phase
    setTimeout(() => {
      isInitialLoad = false;
    }, 500);
  });
})();
