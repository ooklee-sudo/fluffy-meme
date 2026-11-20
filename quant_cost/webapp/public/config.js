// Deployment settings. Edit before collecting real data.
var APP_CONFIG = {
  // Prolific "study completion" URL (copy it from the Prolific study settings), e.g.
  // "https://app.prolific.com/submissions/complete?cc=XXXXXXXX". Leave empty while testing.
  completeUrl: "https://app.prolific.com/submissions/complete?cc=C1DFHXYI",
  // Where participants who are not eligible are sent (decide the screen-out procedure in Prolific). May stay empty.
  screenoutUrl: "",
  // Seconds before the completion page redirects automatically (0 = show a button only).
  redirectAfterSeconds: 0
};
