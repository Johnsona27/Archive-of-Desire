
const button = document.getElementById("connectButton");
const statusText = document.getElementById("status");
const description = document.getElementById("description");
const videoTrack = document.getElementById("videoTrack");

let connected = false;

// Installation sound
const installationAudio = new Audio("sound/Sound%20design.mp3");
installationAudio.loop = true;
installationAudio.preload = "auto";
installationAudio.volume = 0.8;

// Your 31 influencer videos
const videoFiles = Array.from(
  { length: 31 },
  (_, index) =>
    `desire_${String(index + 1).padStart(3, "0")}.mp4`
);

const videoFolder = "assets/DESIRE Influence videos/";

// Build one horizontal group
function createVideoGroup() {
  const group = document.createElement("div");
  group.className = "stream-group";

  const sizes = ["tall", "medium", "square", "wide"];

  videoFiles.forEach((filename, index) => {
    const tile = document.createElement("div");

    tile.className =
      `stream-item video-tile ${sizes[index % sizes.length]}`;

    const video = document.createElement("video");

    video.src = videoFolder + encodeURIComponent(filename);
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = "metadata";

    tile.appendChild(video);
    group.appendChild(tile);
  });

  return group;
}

// Duplicate sequence for seamless scrolling
videoTrack.appendChild(createVideoGroup());
videoTrack.appendChild(createVideoGroup());

// Change system state
function updateSystem() {
  document.body.classList.toggle("connected", connected);

  if (connected) {
    statusText.textContent = "RECONNECTED";
    button.textContent = "DISCONNECT";

    description.textContent =
      "The feed is active. Images circulate. Material accumulates.";

    // Start audio only if it is not already playing
    if (installationAudio.paused) {
      installationAudio.currentTime = 0;

      installationAudio.play().catch(error => {
        console.warn("Audio playback error:", error);
      });
    }

  } else {
    statusText.textContent = "DISCONNECTED";
    button.textContent = "RECONNECT";

    description.textContent =
      "The stream is paused. The accumulated material remains.";

    // Stop and reset audio
    installationAudio.pause();
    installationAudio.currentTime = 0;
  }

  // Start or pause influencer videos
  document.querySelectorAll(".video-tile video")
    .forEach(video => {

      if (connected) {
        video.play().catch(error => {
          console.warn("Video playback error:", error);
        });
      } else {
        video.pause();
      }

    });
}

// Button interaction
button.addEventListener("click", () => {
  connected = !connected;
  updateSystem();
});

/* =====================================
   KEYBOARD CONTROLS
   F8  = RECONNECT
   F10 = DISCONNECT
===================================== */

document.addEventListener("keydown", function(event) {

  if (event.key === "F8") {
    event.preventDefault();

    if (!connected) {
      connected = true;
      updateSystem();
    }
  }

  if (event.key === "F10") {
    event.preventDefault();

    if (connected) {
      connected = false;
      updateSystem();
    }
  }

});

// Initialize disconnected state
updateSystem();
