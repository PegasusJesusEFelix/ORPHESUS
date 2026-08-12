const statusElement = document.getElementById("status");
const resultSection = document.getElementById("result");
const titleElement = document.getElementById("title");
const lyricsElement = document.getElementById("lyrics");
const factsElement = document.getElementById("facts");
const objectivesElement = document.getElementById("objectives");
const audioElement = document.getElementById("audio");
const downloadElement = document.getElementById("download");
const fileUpload = document.getElementById("file-upload");
const contentArea = document.getElementById("content");
const generateButton = document.getElementById("generate");

let selectedFile = null;

fileUpload.addEventListener("change", (event) => {
    selectedFile = event.target.files[0] || null;
    document.getElementById("file-name").textContent = selectedFile
        ? selectedFile.name
        : "TXT, PDF, PNG, JPG, JPEG, WEBP up to 15 MB";
});

async function generateSong() {
    const text = contentArea.value.trim();
    const genre = document.getElementById("genre").value;
    const mood = document.getElementById("mood").value;
    const language = document.getElementById("language").value;

    if (!text && !selectedFile) {
        statusElement.textContent = "Please enter study material or choose a file.";
        return;
    }

    generateButton.disabled = true;
    fileUpload.disabled = true;
    statusElement.textContent = "Creating your learning song...";
    resultSection.classList.add("hidden");

    try {
        const response = selectedFile
            ? await uploadStudyFile(selectedFile, genre, mood, language)
            : await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, genre, mood, language }),
            });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Generation failed.");
        }
        showResult(data);
        statusElement.textContent = "Your song is ready.";
    } catch (error) {
        console.error(error);
        statusElement.textContent = error.message;
    } finally {
        generateButton.disabled = false;
        fileUpload.disabled = false;
    }
}

function uploadStudyFile(file, genre, mood, language) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("genre", genre);
    formData.append("mood", mood);
    formData.append("language", language);
    return fetch("/api/upload", { method: "POST", body: formData });
}

function renderList(element, values) {
    element.innerHTML = "";
    (values || []).forEach((value) => {
        const item = document.createElement("li");
        item.textContent = value;
        element.appendChild(item);
    });
}

function showResult(data) {
    titleElement.textContent = data.title || "ORPHEUS Song";
    document.getElementById("subtitle").textContent = [data.subject, data.topic, data.difficulty]
        .filter(Boolean)
        .join(" - ");
    lyricsElement.textContent = data.lyrics || "";
    renderList(factsElement, data.key_facts);
    renderList(objectivesElement, data.learning_objectives);
    audioElement.src = data.audio_url;
    audioElement.load();
    downloadElement.href = data.audio_url;
    downloadElement.classList.remove("hidden");
    resultSection.classList.remove("hidden");
}

generateButton.addEventListener("click", generateSong);
