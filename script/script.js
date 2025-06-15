let map;
let userLocation = null;
let disasterMarkers = [];
let shelterMarkers = [];

function initMap() {
  map = L.map("map").setView([39.8283, -98.5795], 4);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  loadRecentDisasters();
}

function getLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        userLocation = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };

        map.setView([userLocation.lat, userLocation.lon], 10);

        L.marker([userLocation.lat, userLocation.lon])
          .addTo(map)
          .bindPopup("Your Location")
          .openPopup();

        loadNearbyShelters();

        document.getElementById(
          "status"
        ).textContent = `Location acquired: ${userLocation.lat.toFixed(
          4
        )}, ${userLocation.lon.toFixed(4)}`;
      },
      function (error) {
        document.getElementById("status").textContent =
          "Unable to get your location. You can still ask questions without location.";
      }
    );
  } else {
    document.getElementById("status").textContent =
      "Geolocation is not supported by this browser.";
  }
}

async function loadRecentDisasters() {
  try {
    const response = await fetch("/api/disasters");
    const data = await response.json();

    disasterMarkers.forEach((marker) => map.removeLayer(marker));
    disasterMarkers = [];

    console.log(data.disasters);

    data.disasters.forEach((disaster) => {
      const coords = disaster.coordinates;
      const lat = coords[1];
      const lon = coords[0];

      let icon = "🌋";

      const marker = L.marker([lat, lon], {
        icon: L.divIcon({
          html: icon,
          iconSize: [20, 20],
          className: "disaster-icon",
        }),
      }).addTo(map);

      let popupContent = `<b>Earthquake</b><br>`;
      popupContent += `Location: ${disaster.place}<br>`;

      if (disaster.magnitude) {
        popupContent += `Magnitude: ${disaster.magnitude}<br>`;
      }

      popupContent += `Time: ${new Date(disaster.timestamp).toLocaleString()}`;

      marker.bindPopup(popupContent);
      disasterMarkers.push(marker);
    });

    const disasterListEl = document.getElementById("disasterList");
    if (data.disasters.length === 0) {
      disasterListEl.innerHTML =
        '<div class="disaster-item">No recent disasters found.</div>';
    } else {
      disasterListEl.innerHTML = data.disasters
        .slice(0, 5)
        .map(
          (disaster) =>
            `<div class="disaster-item">
              <p>Time: ${new Date(disaster.timestamp).toLocaleString()}</p>
              <p>${disaster.description}</p>
            </div>`
        )
        .join("");
    }
  } catch (error) {
    console.error("Error loading disasters: ", error);
    document.getElementById("disasterList").innerHTML =
      '<div class="disaster-item">Error loading disaster data.</div>';
  }
}

async function loadNearbyShelters() {
  if (!userLocation) return;

  try {
    const response = await fetch(
      `/api/shelters?lat=${userLocation.lat}&lon=${userLocation.lon}&radius=50`
    );
    const data = await response.json();

    shelterMarkers.forEach((marker) => map.removeLayer(marker));
    shelterMarkers = [];

    data.shelters.forEach((shelter) => {
      const coords = shelter.locations["coordinates"];
      const lat = coords[1];
      const lon = coords[0];
      console.log(shelter);

      let icon = "🏠";

      const marker = L.marker([lat, lon], {
        icon: L.divIcon({
          html: icon,
          iconSize: [20, 20],
          className: "shelter-icon",
        }),
      }).addTo(map);

      let popupContent = `<b>${shelter.name}</b><br>`;
      if (shelter.capacity) {
        popupContent += `Capacity: ${shelter.capacity}<br>`;
      }
      if (shelter.amenities && shelter.amenities.length > 0) {
        popupContent += `Amenities: ${shelter.amenities.join(", ")}<br>`;
      }
      if (shelter.contact_info && shelter.contact_info.phone) {
        popupContent += `Contact: ${shelter.contact_info.phone}<br>`;
      }
      if (shelter.opening_hours) {
        popupContent += `Hours: ${shelter.opening_hours}`;
      }

      marker.bindPopup(popupContent);
      shelterMarkers.push(marker);
    });
  } catch (error) {
    console.error("Error loading shelters:", error);
  }
}

async function askQuestion() {
  const questionInput = document.getElementById("questionInput");
  const question = questionInput.value.trim();

  if (!question) return;

  addMessage(question, "user");
  questionInput.value = "";

  document.getElementById("loading").style.display = "block";

  try {
    const requestBody = {
      question: question,
    };

    if (userLocation) {
      requestBody.latitude = userLocation.lat;
      requestBody.longitude = userLocation.lon;
    }

    const response = await fetch("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    const data = await response.json();

    if (response.ok) {
      addMessage(data.answer, "bot");

      const disasters = data.context.recent_disasters || [];
      const shelters = data.context.nearby_shelters || [];
      document.getElementById(
        "status"
      ).textContent = `Found ${disasters.length} recent disasters and ${shelters.length} nearby shelters.`;
    } else {
      addMessage(
        "Sorry, I encountered an error processing your question. Please try again.",
        "bot"
      );
    }
  } catch (error) {
    console.error("Error asking question:", error);
    addMessage(
      "Sorry, I'm having trouble connecting to the server. Please try again later.",
      "bot"
    );
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}

function addMessage(message, sender) {
  const chatContainer = document.getElementById("chatContainer");
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}-message`;
  messageDiv.innerHTML = message.replace(/\n/g, "<br>");
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function () {
  initMap();

  // Refresh disaster data every 10 minutes
  setInterval(loadRecentDisasters, 600000);
});

window.getLocation = getLocation;
window.askQuestion = askQuestion;
