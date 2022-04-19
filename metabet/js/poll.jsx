import React from 'react';
import PropTypes from 'prop-types';
import { Button, Card, Divider, Image, Placeholder } from 'semantic-ui-react'
import moment from 'moment';

export default class Poll extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = { 
      pollDate: false, // Date of poll (default to false for render sake)
      choices: [], // Choices for a given poll
      description: '', // Description of poll ex. Over/Under Heat Game
      endTime: '', // Time at which poll closes (EST Time)
      pollEnded: false, // Whether the poll has ended (dependent on endTime)
      selection: 'Over 212.5', // Logged in user's selection on the poll 
      submitted: false, // Whether the user has submitted the poll
      poll: {
        date: false
      },
      user: 'jake', // logged in user's id
      vote_url: '/api/votes/', // url for GET vote page
      get_vote_url: '/api/vote/' // url for POST user vote
    };
    this.handleChoiceSelection = this.handleChoiceSelection.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.checkTime = this.checkTime.bind(this);
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
      .catch((error) => console.log(error));
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

    console.log('submitted vote');

    // POST /api/vote/ --> save user's vote to db
    fetch(vote_url, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: cur_user,
        selection: choice 
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
    .catch((error) => console.log(error));

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

    if (poll.date) {
      return (
        <>
          <h1>{moment(poll.endTime).format("MMMM Do, YYYY")}</h1>
          <Divider />
          <h3>{poll.description}</h3>
          <Divider />
          <Card.Group doubling itemsPerRow={poll.numChoices} stackable>
            {choices.map((card) => (
              <Card key={card.choiceName}>
                <Image src={card.avatar} />

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
    return <h1>No Open Polls</h1>
  }
}


// HARD CODED REFERENCE:

// const poll = {
//   date: 'September 29, 2022',
//   description: 'Over/Under Heat Game',
//   endTime: '2022-04-06 11:44:10', 
//   numChoices: 2
// }