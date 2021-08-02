let socket;
try {
  socket = io();
} catch (e) {
  alert("The WebSocket connection failed");
}

function sendUpdate(value) {
  if (value !== 1 && value !== -1) return;
  try {
    socket.emit("update", value);
  } catch (e) {
    console.log(e);
    alert("An error occurred, and the value was not updated.");
  }
}

function receiveUpdate(data) {
  if (data === false) {
    alert("An error occurred, and the most recent record was not recorded.");
    return;
  }
  if (data.length !== 4) {
    alert("Invalid data was received while updating.");
    return;
  }
  updateCount(data[2]);
  addRecord(data[0], data[1], data[2], data[3], data[4]);
}

function addRecord(recordTime, recordUser, recordValue, recordChange) {
  let recordContainer = document.getElementById("records");
  let localizedTime = new Date(
    (recordTime - new Date().getTimezoneOffset() * 60) * 1000
  );
  let timeString = localizedTime.toTimeString().slice(0, 8);

  [
    ["value", recordValue],
    ["user", recordUser],
    ["time", timeString],
  ].forEach(([title, item]) => {
    let recordElement = document.createElement("span");
    recordElement.innerHTML = item.toString();
    recordElement.classList.add("record");
    recordElement.classList.add("newRecord");

    if (recordUser === ownUsername) {
      recordElement.classList.add("ownRecord");
      if (
        title === "value" &&
        document.getElementById("muteControl").classList.contains("checked")
      ) {
        new Audio("/ding.mp3").play();
      }
    }

    if (title === "value") {
      if (recordChange > 0) {
        recordElement.classList.add("positive");
      } else {
        recordElement.classList.add("negative");
      }
    }

    recordContainer.prepend(recordElement);
    setTimeout(() => recordElement.classList.remove("newRecord"), 100);
  });

  while (recordContainer.children.length > 20 * 3) {
    for (let i = 0; i < 3; i++) {
      recordContainer.lastChild.remove();
    }
  }
}

function updateCount(value) {
  let countView = document.getElementById("count");
  countView.innerHTML = value.toString();
  if ((value >= eventMax && eventMax > 0) || value < 0) {
    countView.classList.add("eventValueInvalid");
  } else {
    countView.classList.remove("eventValueInvalid");
  }
}

socket.on("update", receiveUpdate);

socket.on("join", (data) => {
  try {
    if (data === false) {
      throw Error('Server responded "false" to join');
    }
    updateCount(data);
  } catch (e) {
    console.log(e);
    alert(
      "The WebSocket connection was established, but the response was invalid."
    );
  }
});

document.cookie.split(";").some((cookie) => {
  if (cookie.startsWith("session=")) {
    let sessionKey = cookie.slice(8);
    socket.emit("join", sessionKey);
    return true;
  }
});
