function setupCopyButton() {
    const btn = document.getElementById("copy-png-btn");
    if (!btn) {
        // Button not yet loaded, try again soon
        setTimeout(setupCopyButton, 100);
        return;
    }

    btn.onclick = async function () {
        try {
            const graphDiv = document.getElementById("my-graph").querySelector(".js-plotly-plot");
            if (!graphDiv) {
                alert("Graph div not found");
                return;
            }

            const imgData = await Plotly.toImage(graphDiv, { format: 'png', height: 600, width: 800 });
            const res = await fetch(imgData);
            const blob = await res.blob();

            if (!navigator.clipboard) {
                alert("Clipboard API not supported in this browser");
                return;
            }

            await navigator.clipboard.write([
                new ClipboardItem({ "image/png": blob })
            ]);

            alert("Graph copied to clipboard as PNG!");
        } catch (e) {
            alert("Failed to copy image: " + e.message);
            console.error(e);
        }
    };
}

// Start trying to setup the button
setupCopyButton();
