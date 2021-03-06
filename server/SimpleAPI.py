from flask import Flask, jsonify, request
from requests import get
from flask.ext.cors import origin

app = Flask(__name__)
app.config.from_object('configuration')

def get_request_json(url, params={}):
    """
    Helper for sending a get request and getting the returned json.
    """

    auth_params = dict(params)
    auth_params['client_id'] = app.config['GITHUB_CLIENT_ID']
    auth_params['client_secret'] = app.config['GITHUB_CLIENT_SECRET']

    req = get(url, params=auth_params)

    return req.json()

def get_repository_info(request_dict, endpoint):
    """
    Helper for querying the Github repository API.
    """

    params = dict(request_dict)
    # Remove url from request args before passing them to the request
    repo_url = params.pop('q')[0]

    return get_request_json(repo_url + endpoint, params)


@app.route('/search', methods=['GET'])
@origin(app.config['ORIGIN'])
def search():
    """
    Endpoint for calling Github search API.
    Pass the parameters given in the query_string 'as is' so that the user
    is free to use the filters from Github
    Return the JSON sent by the API.
    """

    query_url = app.config['GITHUB_API_SEARCH_URL'] + 'repositories'
    query_data = get_request_json(query_url, request.args)
    return jsonify(query_data)        

@app.route('/commits', methods=['GET'])
@origin(app.config['ORIGIN'])
def commits():
    """
    Endpoint for getting informations on the commits of a repository from the 
    Github API.
    Returns a json object with the dates of the commits in an array under
    'timeline' and a json object with the url of the contributor and the
    number of commits s/he did under the key 'impact'.
    """
    def format_commit(commit):
        """
        Helper for formatting commit.
        Currently only return the date of the commit.
        """

        return commit['author']['date']

    def process_commits(commits):
        """
        Process commits to obtain the data structure exposed in this function
        parent docstring.
        """

        results = {'timeline': []}
        impact = {}
    
        for commit_object in commits:
            results['timeline'].append(format_commit(commit_object['commit']))
            # The top level author object is null on some commit
            # mirroring problem on github end???
            author = commit_object.get('author',None)
            if author is not None:
                author_url = author['url']
                impact[author_url] = impact.get(author_url, 0) + 1
            else:
                impact['anonymous'] = impact.get('anonymous', 0) + 1
                
        results['impact'] = impact

        return results

    return jsonify(process_commits(
        get_repository_info(request.args, '/commits')))

@app.route('/contributors', methods=['GET'])
@origin(app.config['ORIGIN'])
def contributors():
    """
    Endpoint for getting the contributors of a repository from the Github API.
    Returns a list of every contributors on the repository (their Github API
    url) in an array under the 'contributors' key.
    """
    def format_contributors(contributors):
        """
        Return a list of the Github API url of contributors for the repository.
        """
            
        return [ u['url'] for u in contributors ]

    return jsonify(contributors = format_contributors(
        get_repository_info(request.args, '/contributors')))


if __name__ == '__main__':
    app.run()
