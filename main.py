import json

import config
import func
from func import get_request, compile_message, get_hotpool_violations, get_track_slugs, get_tracks_scores

"""
Summary of Functions:

1. get_request(q):
   - Sends a POST request to the configured endpoint with the provided query (q).
   - Uses the Authorization header with the access token from config.
   - Returns the response object.

2. get_track_plays_by_month(track_slugs, org_slug=config.ORG_SLUG, filter_developers=config.FILTER_DEVELOPERS, dates=utilities.month_map(config.YEAR)):
   - Retrieves the number of track plays for the provided track slugs by month.
   - Iterates through the dates and slugs, sending queries to get statistics for each.
   - Returns a table of track plays by month.

3. get_track_slugs():
   - Sends a query to retrieve all track slugs for the organization.
   - Returns a list of slugs.

5. get_slugs_with_tag(tag_val):
   - Sends a query to retrieve track slugs with a specific tag value.
   - Writes the tagged slugs to a file in the outputs directory.
   - Returns a list of tagged slugs.

6. write_list_to_file(lines, name):
   - Writes a list of lines to a text file in the outputs directory.
   - The file is named using the provided name parameter.

7. is_token_valid():
   - Reads the Instruqt credentials file from ~/.config/instruqt/credentials.
   - Checks if the stored token is still valid based on the expiration time.
   - Returns True if valid, False otherwise.

8. renew_token():
   - Runs the "instruqt auth login" command to renew the token if it's expired.
   - Prints a success or error message based on the command's execution.

9. check_and_renew_token():
   - Checks if the Instruqt token is valid using is_token_valid().
   - If the token is expired, renew_token() is called to renew the token.
"""


def main():
    # func.check_and_renew_token()

    get_hotpool_violations()

    tracks_tagged = func.get_slugs_with_tag("terraform")
    #
    # tracks_all = func.get_track_slugs()
    #
    # func.get_track_plays_by_month(tracks_tagged)

    hvd_tracks = ["health-assessments-and-run-tasks",
                  "terraform-modules-testing-and-lifecycle",
                  "vcdl-888-sentinel-module-development",
                  "sentinel-pac-lifecycle-management",
                  "terraform-agents",
                  "terraform-git-flow",
                  "terraform-cloud-consumer-workflow",
                  "terraform-cloud-variables",
                  "dynamic-credentials-terraform-cloud",
                  "terraform-control-workspaces",
                  "terraform-landing-zone-provisioning-workflow",
                  "terraform-modules",
                  "terraform-packer",
                  "policy-as-code-introduction-terraform",
                  "tfc-private-module-registry",
                  "tfc-proj-wkspc-conf",
                  "autopilot-configuration-and-operations",
                  "database-secrets-engine",
                  "deployment-and-backup-basics",
                  "vault-dr-recovery-operations",
                  "enterprise-cluster-audit-logs",
                  "hvd-enterprise-cluster-configuration-policy--governance-exercise",
                  "using-vault-basic-concepts",
                  "mfa-with-vault-enterprise",
                  "vault-agent-templating-and-pki-workflow-hvd",
                  "vault-agent-templating-and-pki",
                  "vault-authentication-basics",
                  "vault-dynamic-secrets-with-cloud-engines-hvd",
                  "vault-static-secret-basics",
                  "consul-enterprise-business-continuity-and-upgrade",
                  "enterprise-cluster-configuration",
                  "enterprise-cluster-dns-configuration"]

    # query = f"""query {{
    #            tracks(organizationSlug: "{config.ORG_SLUG}") {{
    #              slug
    #              statistics {{
    #                 title
    #                 started_total
    #                 completed_total
    #                 average_review_score
    #                 }}
    #            }}
    #        }}"""
    #
    # print(get_request(query))
    #
    #
    # get_tracks_scores("scores")




if __name__ == "__main__":
    main()
