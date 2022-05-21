import React from 'react';
import { Button, Card, Divider, Image, Placeholder } from 'semantic-ui-react'
import moment from 'moment';
// import { Amplify, Auth, Storage , AmplifyS3Image } from 'aws-amplify';
import { ConnectMetamaskButtonComponent } from './Metamask';

export default class Poll extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = { 
      choices: [], // Choices for a given poll
      pollEnded: false, // Whether the poll has ended (dependent on endTime)
      selection: 'Over 212.5', // Logged in user's selection on the poll 
      submitted: false, // Whether the user has submitted the poll
      poll: {
        date: false // Date of poll (default to false for render sake)
      },
      user: 'jake', // logged in user's id
      vote_url: '/api/votes/', // url for GET vote page
      get_vote_url: '/api/vote/', // url for POST user vote,
      error: { // whether there was an error in backend request
        exists: false,
        message: ''
      }
    };
    this.handleChoiceSelection = this.handleChoiceSelection.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.checkTime = this.checkTime.bind(this);

    // Amplify.configure({
    //   Auth: {
    //       identityPoolId: 'us-east-1:c0022f66-7372-4e53-a314-2a17ba536933', //REQUIRED - Amazon Cognito Identity Pool ID
    //       region: 'us-east-1' // REQUIRED - Amazon Cognito Region
    //   },
    //   Storage: {
    //       AWSS3: {
    //           bucket: 'metabet-choice-uploads' //REQUIRED -  Amazon S3 bucket name
    //       }
    //   }
    // });
  }

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const url = this.state.get_vote_url;
    const cur_user = this.state.user;

    // Set up 10 second timer to check for current time and whether the poll has closed
    this.checkTime();
    const interval = setInterval(this.checkTime, 10000);
    this.setState({
      time_interval: interval
    });

    // Call REST API to get the current day's poll information
    fetch(url + cur_user, {
      credentials: 'same-origin' 
    })
      .then((response) => {
        console.log(response);
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        console.log(data);
        this.setState({
          poll: data.poll,
          choices: data.choices,
          submitted: data.voted,
          selection: data.selection
        });
      })
      .catch((e) => {
        this.setState({
          error: {
            exists: true,
            message: e.message
          }
        });
        console.log(e);
      });
  }

  componentWillUnmount() {
    // Clear the time interval
    const int = this.state.time_interval;
    clearInterval(int);
  }

  handleSubmit() {
    const vote_url = this.state.vote_url;
    const choice = this.state.selection;
    const cur_user = this.state.user;
    const poll = this.state.poll;

    console.log('submitted vote');

    // POST /api/vote/ --> save user's vote to db
    fetch(vote_url, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: cur_user, //TODO: set equal to logged in metamask 
        selection: choice,
        poll_id: poll.poll_id
      }),
      credentials: 'same-origin' 
    })
    .then((response) => {
      console.log(response);
      if (!response.ok) throw Error(response.statusText);
      this.setState({
        submitted: true
      });
    })
    .catch((error) => {
      this.setState({
        error: {
          exists: true,
          message: 'Error Submitting User Vote. Please Try Again.'
        }      
      })
      console.log(error);
    });

  }

  handleChoiceSelection(e, choiceName) {
    console.log('chose an option');
    this.setState({
      selection: choiceName
    });
  }

  checkTime() {
    const poll = this.state.poll;
    console.log(moment());
    console.log(moment(poll.endTime));
    this.setState({
      pollEnded: moment().isAfter(moment(poll.endTime))
    });
  }

  render() {
    const pollEnded = this.state.pollEnded;
    const selection = this.state.selection;
    const submitted = this.state.submitted;
    const poll = this.state.poll;
    const choices = this.state.choices;
    const error = this.state.error

    console.log(choices);
    console.log(poll.endTime);

    if (error.exists) {
      return <h1>{error.message}</h1>
    }
    else if (poll.date) {
      <ConnectMetamaskButtonComponent />
      return (
        <>
          <h1>{moment.utc(poll.date).format("MMMM Do, YYYY")}</h1>
          <Divider />
          <h2>Round {poll.round}</h2>
          <Divider />
          <h3>{poll.description}</h3>
          <Divider />
          <Card.Group doubling itemsPerRow={poll.numChoices} stackable>
            {choices.map((card) => (
              <Card key={card.choiceName}>
                {/* <Image src={card.avatar} /> */}
                {/* <AmplifyS3Image 
                  imgKey='Oahu_Pic.jpeg'
                  path='metabet/static/uploads'
                  identityId='us-east-1:c0022f66-7372-4e53-a314-2a17ba536933'
                /> */}

                <Card.Content>
                    <>
                      <Card.Header>{card.choiceName}</Card.Header>
                    </>
                </Card.Content>

                <Card.Content extra>
                  <Button disabled={selection === card.choiceName || submitted || pollEnded} onClick={(e) => this.handleChoiceSelection(e,card.choiceName)} primary={selection === card.choiceName}>
                    {selection === card.choiceName ? 'Selected' : 'Select'}
                  </Button>
                </Card.Content>
              </Card>
            ))}
          </Card.Group>

          <Divider></Divider>

          <Button disabled={submitted || pollEnded} onClick={this.handleSubmit.bind(this)} primary>{submitted ? 'Vote Submitted!' : 'Submit Choice'}</Button>
          <h2>{pollEnded ? 'Poll Ended' : 'Poll Ends '} {!pollEnded && moment.utc(poll.endTime).fromNow()} </h2>
        </>
      )
    }
    return (
      <>  
        <ConnectMetamaskButtonComponent />
        <h1>No Open Polls</h1>
      </>
    )
  }
}
