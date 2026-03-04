const { JobsClient } = require('@google-cloud/run').v2;
const runClient = new JobsClient({
    projectId: 'polysub',
    keyFilename: 'C:\\Users\\46760\\Downloads\\polysub-f9aa64b5d040.json'
});

async function main() {
    const projectId = 'polysub';
    const region = 'europe-north1';
    const jobName = 'polysub-processor-job';
    const name = runClient.jobPath(projectId, region, jobName);

    const runRequest = {
        name,
        overrides: {
            containerOverrides: [
                {
                    name: "polysub-worker-1",
                    env: [
                        { name: "VIDEO_FILENAME", value: "testing_overrides.mp4" }
                    ]
                }
            ]
        }
    };

    try {
        console.log("Triggering job...");
        const [execution] = await runClient.runJob(runRequest);
        console.log("Job triggered successfully:", execution.name);
    } catch (e) {
        console.error("Error triggering job:", e.message);
    }
}

main();
