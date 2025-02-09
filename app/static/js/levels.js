document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");

    // Initialize MDB tabs
    const tabElements = document.querySelectorAll('[data-mdb-toggle="pill"], [data-mdb-toggle="tab"]');
    tabElements.forEach(tab => {
        new mdb.Tab(tab);
    });

    // Get the fragment identifier from the URL (e.g., #level-2-track-1)
    const fragment = window.location.hash;
    console.log("Fragment:", fragment);

    if (fragment) {
        // Extract level and track IDs from the fragment
        const [levelFragment, trackFragment] = fragment.split('-track-');
        const levelId = levelFragment.replace('#level-', '');
        const trackId = trackFragment || null; // Handle missing track ID

        console.log("Level ID:", levelId);
        console.log("Track ID:", trackId);

        // Activate the level tab
        const levelTabButton = document.getElementById(`level-${levelId}-tab`);
        if (levelTabButton) {
            console.log("Level Tab Button Found:", levelTabButton);
            console.log("Level Tab Button Attributes:", levelTabButton.attributes);

            // Use MDB API to show the tab
            const tabInstance = new mdb.Tab(levelTabButton);
            tabInstance.show();

            // Wait for the level tab content to load using MutationObserver
            const levelTabContent = document.querySelector(`#level-${levelId}`);
            if (levelTabContent) {
                const observer = new MutationObserver((mutationsList, observer) => {
                    // Check if the level tab content is visible
                    if (levelTabContent.classList.contains('show')) {
                        console.log("Level Tab Content Loaded");
                        observer.disconnect(); // Stop observing

                        // Activate the "Full Tracks" pill within the level tab
                        const tracksPill = document.querySelector(`#tracks-${levelId}-tab`);
                        if (tracksPill) {
                            console.log("Tracks Pill Found:", tracksPill);
                            new mdb.Tab(tracksPill).show();

                            // Wait for the "Full Tracks" tab content to load using MutationObserver
                            const tracksTabContent = document.querySelector(`#tracks-${levelId}`);
                            if (tracksTabContent) {
                                const tracksObserver = new MutationObserver((mutationsList, observer) => {
                                    // Check if the "Full Tracks" tab content is visible
                                    if (tracksTabContent.classList.contains('show')) {
                                        console.log("Tracks Tab Content Loaded");
                                        observer.disconnect(); // Stop observing

                                        if (trackId) {
                                            // Look for the Track Tab button using the correct selector
                                            const trackTabButton = document.getElementById(`track-${trackId}-${levelId}-tab`);
                                            console.log("Track Tab Button:", trackTabButton);

                                            if (trackTabButton) {
                                                console.log("Track Tab Button Found:", trackTabButton);
                                                new mdb.Tab(trackTabButton).show();

                                                // Update the URL fragment to reflect the active track tab
                                                window.location.hash = `#level-${levelId}-track-${trackId}`;
                                                console.log("URL Fragment Updated:", window.location.hash);
                                            } else {
                                                console.error("Track Tab Button Not Found");
                                            }
                                        } else {
                                            console.error("Track ID is missing");
                                        }
                                    }
                                });

                                // Start observing the "Full Tracks" tab content
                                tracksObserver.observe(tracksTabContent, {
                                    attributes: true, // Watch for attribute changes
                                    attributeFilter: ['class'] // Only watch for class changes
                                });
                            } else {
                                console.error("Tracks Tab Content Not Found");
                            }
                        } else {
                            console.error("Tracks Pill Not Found");
                        }
                    }
                });

                // Start observing the level tab content
                observer.observe(levelTabContent, {
                    attributes: true, // Watch for attribute changes
                    attributeFilter: ['class'] // Only watch for class changes
                });
            } else {
                console.error("Level Tab Content Not Found");
            }
        } else {
            console.error("Level Tab Button Not Found");
        }
    } else {
        console.log("No Fragment Found");
    }
});