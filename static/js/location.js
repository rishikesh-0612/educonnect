
document.addEventListener("DOMContentLoaded", function () {

    // Detect registration form
    const form = document.getElementById("studentForm") ||
                 document.getElementById("teacherForm");

    if (!form) {
        console.error("Registration form not found!");
        return;
    }

    // Check Leaflet
    if (typeof L === "undefined") {
        alert("Map library failed to load. Check your internet connection.");
        return;
    }

    // Map elements
    const mapElement = document.getElementById("map");
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");
    const locationBtn = document.getElementById("locationBtn");
    const stopBtn = document.getElementById("stopBtn");
    const locationBtnText = document.getElementById("locationBtnText");

    if (!mapElement || !latitudeInput || !longitudeInput ||
        !locationBtn || !stopBtn || !locationBtnText) {
        console.error("One or more location elements are missing.");
        return;
    }

    // Initialize map
    const map = L.map("map").setView([17.3850, 78.4867], 12);

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        {
            maxZoom: 19,
            attribution: "Tiles &copy; Esri"
        }
    ).addTo(map);

    let marker = null;
    let watchId = null;

    // Update coordinates and marker
    function updateLocation(lat, lng) {

        latitudeInput.value = lat.toFixed(7);
        longitudeInput.value = lng.toFixed(7);

        const position = [lat, lng];

        if (marker) {
            marker.setLatLng(position);
        } else {
            marker = L.marker(position).addTo(map);
        }

        marker.bindPopup("Your Selected Location").openPopup();
        map.setView(position, 16);
    }

    // Start live location
    locationBtn.addEventListener("click", function () {

        if (!navigator.geolocation) {
            alert("Your browser does not support location.");
            return;
        }

        if (watchId !== null) {
            stopTracking();
            return;
        }

        locationBtnText.textContent = "Getting Location...";

        watchId = navigator.geolocation.watchPosition(

            function (position) {

                updateLocation(
                    position.coords.latitude,
                    position.coords.longitude
                );

                locationBtnText.textContent = "Tracking... Click to Stop";
            },

            function (error) {

                stopTracking();

                if (error.code === 1) {
                    alert("Please allow location permission in browser settings.");
                } else if (error.code === 2) {
                    alert("Location unavailable. Check your device location.");
                } else {
                    alert("Location request timed out. Try again.");
                }
            },

            {
                enableHighAccuracy: true,
                maximumAge: 5000,
                timeout: 20000
            }
        );
    });

    // Stop tracking
    function stopTracking() {

        if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }

        locationBtnText.textContent = "Start Live Location";
    }

    stopBtn.addEventListener("click", stopTracking);

    // Dynamic subjects for student form
    const gradeSelect = document.getElementById("grade");
    const subjectList = document.getElementById("subjectList");

    if (gradeSelect && subjectList) {
        const subjectsMap = {
            "default": ["Mathematics", "General Science", "Social Studies", "English", "Hindi", "Computer Science"],
            "senior": ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Commerce", "Economics", "English"]
        };

        function renderSubjects() {
            const grade = gradeSelect.value;
            if (!grade) {
                subjectList.innerHTML = '<p style="color:#777; font-size:13px; grid-column: 1 / -1;">Select your class to view subjects.</p>';
                return;
            }

            const list = (grade === "Class 11" || grade === "Class 12") ? subjectsMap.senior : subjectsMap.default;

            subjectList.innerHTML = list.map(subject => `
                <label class="subject-option">
                    <input type="checkbox" name="subjects" value="${subject}">
                    ${subject}
                </label>
            `).join("");
        }

        gradeSelect.addEventListener("change", renderSubjects);
    }

    // Select location manually on map
    map.on("click", function (event) {

        stopTracking();

        updateLocation(
            event.latlng.lat,
            event.latlng.lng
        );
    });

    // Form validation
    form.addEventListener("submit", function (event) {

        const password = form.querySelector('[name="password"]').value;
        const confirmPassword =
            form.querySelector('[name="confirm_password"]').value;

        const subjects = form.querySelectorAll(
            'input[name="subjects"]:checked'
        );

        const consent = document.getElementById("location_consent").checked;

        if (password !== confirmPassword) {
            event.preventDefault();
            alert("Passwords do not match.");
            return;
        }

        if (subjects.length === 0) {
            event.preventDefault();
            alert("Please select at least one subject.");
            return;
        }

        if (!latitudeInput.value || !longitudeInput.value) {
            event.preventDefault();
            alert("Please select your location.");
            return;
        }

        if (!consent) {
            event.preventDefault();
            alert("Please agree to location sharing.");
            return;
        }
    });

    window.addEventListener("pagehide", stopTracking);

});
